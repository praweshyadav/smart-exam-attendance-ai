import numpy as np

from backend.ai.face_database import FaceDatabase
from backend.core.config import FACE_RECOGNITION_THRESHOLD


class FaceMatcher:
    """
    Compares a face embedding against registered
    student face embeddings.
    """

    def __init__(
        self,
        database=None,
        threshold=FACE_RECOGNITION_THRESHOLD
    ):
        self.database = database or FaceDatabase()
        self.threshold = threshold

    @staticmethod
    def cosine_similarity(embedding_a, embedding_b):
        """
        Calculate cosine similarity between two embeddings.
        """

        embedding_a = np.asarray(
            embedding_a,
            dtype=np.float32
        )

        embedding_b = np.asarray(
            embedding_b,
            dtype=np.float32
        )

        if embedding_a.shape != (512,):
            raise ValueError(
                "First embedding must have shape (512,)."
            )

        if embedding_b.shape != (512,):
            raise ValueError(
                "Second embedding must have shape (512,)."
            )

        norm_a = np.linalg.norm(embedding_a)
        norm_b = np.linalg.norm(embedding_b)

        if norm_a == 0 or norm_b == 0:
            raise ValueError(
                "Embedding cannot have zero magnitude."
            )

        similarity = np.dot(
            embedding_a,
            embedding_b
        ) / (norm_a * norm_b)

        return float(similarity)

    def find_best_match(self, embedding):
        """
        Find the registered student with the highest cosine similarity.
        Optimized with vectorized matrix dot product across all registered embeddings.
        """
        if embedding is None:
            return {
                "student_id": None,
                "similarity": None,
                "matched": False,
            }

        embedding = np.asarray(
            embedding,
            dtype=np.float32,
        )

        if embedding.shape != (512,):
            raise ValueError(
                "Embedding must have shape (512,)."
            )

        norm = np.linalg.norm(embedding)
        if norm == 0:
            return {
                "student_id": None,
                "similarity": 0.0,
                "matched": False,
            }

        query_unit = embedding / norm

        student_ids, matrix = self.database.get_embeddings_matrix()

        if len(student_ids) == 0 or matrix.shape[0] == 0:
            return {
                "student_id": None,
                "similarity": None,
                "matched": False,
            }

        # Vectorized BLAS matrix-vector dot product computes similarities for all students at once
        similarities = np.dot(matrix, query_unit)
        best_idx = int(np.argmax(similarities))
        best_similarity = float(similarities[best_idx])
        best_student_id = student_ids[best_idx]

        matched = best_similarity >= self.threshold

        if not matched:
            best_student_id = None

        return {
            "student_id": best_student_id,
            "similarity": best_similarity,
            "matched": matched,
        }