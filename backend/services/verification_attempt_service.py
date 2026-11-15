import time
from backend.database.database import get_connection


class VerificationAttemptService:
    """
    Handles storage and retrieval of student verification attempts.
    Features an in-memory duplicate cooldown to prevent database flooding.
    """

    def __init__(self):
        self._recent_attempts = {}

    def record_attempt(
        self,
        student_id=None,
        result="Failed",
        similarity=None,
        liveness_result=None,
        reason=None,
        face_image=None,
    ):
        """
        Record a verification attempt with a 4-second throttle for duplicate attempts.

        Returns:
            int: ID of the recorded attempt.
        """

        result = result.strip()

        if not result:
            raise ValueError(
                "Verification result cannot be empty."
            )

        now = time.time()
        dedup_key = (student_id, result)
        last_rec = self._recent_attempts.get(dedup_key)
        if last_rec and (now - last_rec[0]) < 4.0:
            return last_rec[1]

        with get_connection() as connection:

            cursor = connection.execute(
                """
                INSERT INTO verification_attempts (
                    student_id,
                    result,
                    similarity,
                    liveness_result,
                    reason,
                    face_image
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    result,
                    similarity,
                    liveness_result,
                    reason,
                    face_image,
                ),
            )

            connection.commit()
            last_id = cursor.lastrowid
            self._recent_attempts[dedup_key] = (now, last_id)
            return last_id

    def get_attempt(self, attempt_id):
        """
        Retrieve one verification attempt.

        Returns:
            dict or None
        """

        with get_connection() as connection:

            attempt = connection.execute(
                """
                SELECT
                    id,
                    student_id,
                    timestamp,
                    result,
                    similarity,
                    liveness_result,
                    reason
                FROM verification_attempts
                WHERE id = ?
                """,
                (attempt_id,),
            ).fetchone()

        if attempt is None:
            return None

        return dict(attempt)

    def get_all_attempts(self):
        """
        Retrieve all verification attempts.

        Returns:
            list of dictionaries
        """

        with get_connection() as connection:

            attempts = connection.execute(
                """
                SELECT
                    id,
                    student_id,
                    timestamp,
                    result,
                    similarity,
                    liveness_result,
                    reason
                FROM verification_attempts
                ORDER BY timestamp DESC
                """
            ).fetchall()

        return [
            dict(attempt)
            for attempt in attempts
        ]

    def get_attempts_by_student(self, student_id):
        """
        Retrieve verification attempts
        for a specific student.
        """

        with get_connection() as connection:

            attempts = connection.execute(
                """
                SELECT
                    id,
                    student_id,
                    timestamp,
                    result,
                    similarity,
                    liveness_result,
                    reason
                FROM verification_attempts
                WHERE student_id = ?
                ORDER BY timestamp DESC
                """,
                (student_id,),
            ).fetchall()

        return [
            dict(attempt)
            for attempt in attempts
        ]

    def get_attempts_by_result(self, result):
        """
        Retrieve attempts with a specific result.

        Example:
            Success
            Failed
        """

        result = result.strip()

        if not result:
            raise ValueError(
                "Verification result cannot be empty."
            )

        with get_connection() as connection:

            attempts = connection.execute(
                """
                SELECT
                    id,
                    student_id,
                    timestamp,
                    result,
                    similarity,
                    liveness_result,
                    reason
                FROM verification_attempts
                WHERE result = ?
                ORDER BY timestamp DESC
                """,
                (result,),
            ).fetchall()

        return [
            dict(attempt)
            for attempt in attempts
        ]

    def get_failed_attempts(self):
        """
        Retrieve all failed verification attempts.
        """

        return self.get_attempts_by_result(
            "Failed"
        )

    def delete_attempt(self, attempt_id):
        """
        Delete one verification attempt.

        Returns:
            bool: True if deleted.
        """

        with get_connection() as connection:

            existing_attempt = connection.execute(
                """
                SELECT id
                FROM verification_attempts
                WHERE id = ?
                """,
                (attempt_id,),
            ).fetchone()

            if existing_attempt is None:
                return False

            connection.execute(
                """
                DELETE FROM verification_attempts
                WHERE id = ?
                """,
                (attempt_id,),
            )

            connection.commit()

        return True

    def attempt_exists(self, attempt_id):
        """
        Check whether a verification attempt exists.
        """

        with get_connection() as connection:

            attempt = connection.execute(
                """
                SELECT id
                FROM verification_attempts
                WHERE id = ?
                """,
                (attempt_id,),
            ).fetchone()

        return attempt is not None