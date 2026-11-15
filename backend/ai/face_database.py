import time
from pathlib import Path
import pickle

import numpy as np

from backend.core.config import FACE_DATABASE_PATH


class FaceDatabase:
    """
    Handles storage and retrieval of face embeddings,
    synchronized between local disk cache and MySQL database.
    Optimized with pre-stacked normalized 2D vector matrix for ultra-fast matching.
    """

    def __init__(self, database_path=FACE_DATABASE_PATH):
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self._last_mtime = 0
        self._last_check_time = 0
        self._database = self._load_database()
        self._student_ids = []
        self._matrix = np.empty((0, 512), dtype=np.float32)
        self._rebuild_matrix()

    def _rebuild_matrix(self):
        """
        Build pre-normalized 2D matrix for vectorized BLAS similarity search.
        """
        if not self._database:
            self._student_ids = []
            self._matrix = np.empty((0, 512), dtype=np.float32)
            return

        ids = list(self._database.keys())
        mat = np.array([self._database[i] for i in ids], dtype=np.float32)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._matrix = mat / norms
        self._student_ids = ids

    def _sync_with_db(self, data_dict):
        """
        Populate embeddings from MySQL if any are missing from disk.
        """
        try:
            from backend.database.database import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT student_id, face_embedding
                    FROM students
                    WHERE face_registered = 1 AND face_embedding IS NOT NULL
                    """
                ).fetchall()
                for r in rows:
                    sid = r.get("student_id")
                    raw_blob = r.get("face_embedding")
                    if raw_blob and sid not in data_dict:
                        try:
                            emb = pickle.loads(raw_blob)
                            if isinstance(emb, np.ndarray) and emb.shape == (512,):
                                data_dict[sid] = emb
                        except Exception:
                            pass
        except Exception:
            pass
        return data_dict

    def _load_database(self):
        """
        Load the face database from disk and MySQL.
        """
        database = {}
        if self.database_path.exists():
            try:
                with open(self.database_path, "rb") as file:
                    loaded = pickle.load(file)
                if isinstance(loaded, dict):
                    database = loaded
                self._last_mtime = self.database_path.stat().st_mtime
            except Exception:
                database = {}

        database = self._sync_with_db(database)
        return database

    def _check_and_reload(self):
        """
        Check if file on disk was modified by another process and reload if needed.
        Rate-limited to avoid excessive filesystem stat calls.
        """
        now = time.time()
        if now - getattr(self, "_last_check_time", 0) < 2.0:
            return
        self._last_check_time = now
        try:
            if self.database_path.exists():
                mtime = self.database_path.stat().st_mtime
                if mtime > getattr(self, "_last_mtime", 0):
                    self._database = self._load_database()
                    self._last_mtime = mtime
                    self._rebuild_matrix()
            else:
                self._database = self._sync_with_db({})
                self._last_mtime = 0
                self._rebuild_matrix()
        except Exception:
            pass

    def _save_database(self):
        """
        Save the face database to disk.
        """
        with open(self.database_path, "wb") as file:
            pickle.dump(self._database, file)
        try:
            self._last_mtime = self.database_path.stat().st_mtime
        except Exception:
            pass

    def _save_to_mysql(self, student_id, embedding):
        """
        Persist the face embedding to MySQL.
        """
        try:
            from backend.database.database import get_connection
            with get_connection() as conn:
                blob = pickle.dumps(np.asarray(embedding, dtype=np.float32))
                conn.execute(
                    """
                    UPDATE students
                    SET face_embedding = ?, face_registered = 1
                    WHERE student_id = ?
                    """,
                    (blob, student_id)
                )
                conn.commit()
        except Exception:
            pass

    def _delete_from_mysql(self, student_id):
        """
        Remove the face embedding from MySQL.
        """
        try:
            from backend.database.database import get_connection
            with get_connection() as conn:
                conn.execute(
                    """
                    UPDATE students
                    SET face_embedding = NULL, face_registered = 0
                    WHERE student_id = ?
                    """,
                    (student_id,)
                )
                conn.commit()
        except Exception:
            pass

    def save_embedding(self, student_id, embedding):
        """
        Save a new face embedding for a student.

        Returns:
            bool: True if saved, False if already exists.
        """
        self._check_and_reload()

        if not student_id:
            raise ValueError(
                "Student ID cannot be empty."
            )

        embedding = np.asarray(embedding, dtype=np.float32)

        if embedding.shape != (512,):
            raise ValueError(
                "Face embedding must have shape (512,)."
            )

        if student_id in self._database:
            return False

        self._database[student_id] = embedding
        self._rebuild_matrix()
        self._save_database()
        self._save_to_mysql(student_id, embedding)

        return True

    def get_embedding(self, student_id):
        """
        Retrieve a student's face embedding.

        Returns:
            numpy.ndarray or None
        """
        self._check_and_reload()
        return self._database.get(student_id)

    def update_embedding(self, student_id, embedding):
        """
        Update an existing student's face embedding.

        Returns:
            bool: True if updated, False if student does not exist.
        """
        self._check_and_reload()

        if not student_id:
            raise ValueError(
                "Student ID cannot be empty."
            )

        embedding = np.asarray(embedding, dtype=np.float32)

        if embedding.shape != (512,):
            raise ValueError(
                "Face embedding must have shape (512,)."
            )

        self._database[student_id] = embedding
        self._rebuild_matrix()
        self._save_database()
        self._save_to_mysql(student_id, embedding)

        return True

    def delete_embedding(self, student_id):
        """
        Delete a student's face embedding.

        Returns:
            bool: True if deleted, False if not found.
        """
        self._check_and_reload()

        if student_id not in self._database:
            return False

        del self._database[student_id]
        self._rebuild_matrix()
        self._save_database()
        self._delete_from_mysql(student_id)

        return True

    def get_embeddings_matrix(self):
        """
        Return a tuple of (student_ids, pre-normalized 2D numpy matrix of shape (N, 512)).
        Allows matrix BLAS dot product for vector similarity search in microseconds.
        """
        self._check_and_reload()
        return self._student_ids, self._matrix

    def embedding_exists(self, student_id):
        """
        Check whether a student's face embedding exists.
        """
        self._check_and_reload()
        return student_id in self._database

    def get_all_embeddings(self):
        """
        Return all stored face embeddings.
        """
        self._check_and_reload()
        return self._database.copy()

    def count(self):
        """
        Return the number of stored face embeddings.
        """
        self._check_and_reload()
        return len(self._database)
