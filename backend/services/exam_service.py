from backend.database.database import get_connection
from backend.services.activity_service import log_activity
from backend.services.notification_service import create_notification


def add_exam(
    exam_name,
    class_id,
    exam_date,
    start_time=None
):
    exam_name = exam_name.strip()
    exam_date = exam_date.strip()

    if not exam_name:
        raise ValueError("Exam name cannot be empty.")

    if not exam_date:
        raise ValueError("Exam date cannot be empty.")

    with get_connection() as connection:

        # Verify that the class exists
        existing_class = connection.execute(
            """
            SELECT class_id
            FROM classes
            WHERE class_id = ?
            """,
            (class_id,)
        ).fetchone()

        if existing_class is None:
            raise ValueError("Class does not exist.")

        cursor = connection.execute(
            """
            INSERT INTO exams (
                exam_name,
                class_id,
                exam_date,
                start_time
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                exam_name,
                class_id,
                exam_date,
                start_time
            )
        )

        connection.commit()
        ex_id = cursor.lastrowid

    log_activity(
        "EXAM_CREATED",
        f"Exam created: {exam_name} for date {exam_date}",
        "exam",
        str(ex_id)
    )
    create_notification(
        "Exam Scheduled",
        f"Exam '{exam_name}' scheduled for {exam_date}.",
        "info"
    )

    return True


def get_exam(exam_id):
    with get_connection() as connection:
        exam = connection.execute(
            """
            SELECT
                exam_id,
                exam_name,
                class_id,
                exam_date,
                start_time,
                created_at
            FROM exams
            WHERE exam_id = ?
            """,
            (exam_id,)
        ).fetchone()

    if exam is None:
        return None

    return dict(exam)


def get_all_exams():
    with get_connection() as connection:
        exams = connection.execute(
            """
            SELECT
                exam_id,
                exam_name,
                class_id,
                exam_date,
                start_time,
                created_at
            FROM exams
            ORDER BY exam_date, start_time
            """
        ).fetchall()

    return [dict(exam) for exam in exams]


def get_exams_by_class(class_id):
    with get_connection() as connection:
        exams = connection.execute(
            """
            SELECT
                exam_id,
                exam_name,
                class_id,
                exam_date,
                start_time,
                created_at
            FROM exams
            WHERE class_id = ?
            ORDER BY exam_date, start_time
            """,
            (class_id,)
        ).fetchall()

    return [dict(exam) for exam in exams]


def update_exam(
    exam_id,
    exam_name=None,
    class_id=None,
    exam_date=None,
    start_time=None
):
    with get_connection() as connection:

        existing_exam = connection.execute(
            """
            SELECT exam_id
            FROM exams
            WHERE exam_id = ?
            """,
            (exam_id,)
        ).fetchone()

        if existing_exam is None:
            return False

        updates = []
        values = []

        if exam_name is not None:
            exam_name = exam_name.strip()

            if not exam_name:
                raise ValueError("Exam name cannot be empty.")

            updates.append("exam_name = ?")
            values.append(exam_name)

        if class_id is not None:
            existing_class = connection.execute(
                """
                SELECT class_id
                FROM classes
                WHERE class_id = ?
                """,
                (class_id,)
            ).fetchone()

            if existing_class is None:
                raise ValueError("Class does not exist.")

            updates.append("class_id = ?")
            values.append(class_id)

        if exam_date is not None:
            exam_date = exam_date.strip()

            if not exam_date:
                raise ValueError("Exam date cannot be empty.")

            updates.append("exam_date = ?")
            values.append(exam_date)

        if start_time is not None:
            updates.append("start_time = ?")
            values.append(start_time)

        if not updates:
            return True

        values.append(exam_id)

        connection.execute(
            f"""
            UPDATE exams
            SET {", ".join(updates)}
            WHERE exam_id = ?
            """,
            values
        )

        connection.commit()

    return True


def delete_exam(exam_id):
    with get_connection() as connection:

        existing_exam = connection.execute(
            """
            SELECT exam_id
            FROM exams
            WHERE exam_id = ?
            """,
            (exam_id,)
        ).fetchone()

        if existing_exam is None:
            return False

        connection.execute(
            """
            DELETE FROM exams
            WHERE exam_id = ?
            """,
            (exam_id,)
        )

        connection.commit()

    return True


def exam_exists(exam_id):
    with get_connection() as connection:
        exam = connection.execute(
            """
            SELECT exam_id
            FROM exams
            WHERE exam_id = ?
            """,
            (exam_id,)
        ).fetchone()

    return exam is not None