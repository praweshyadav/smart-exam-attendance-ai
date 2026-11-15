from backend.database.database import get_connection
from backend.services.holiday_service import check_attendance_allowed
from backend.services.activity_service import log_activity


def mark_attendance(
    session_id,
    student_id,
    student_name,
    attendance_date,
    attendance_time,
    status="Present",
    verification_score=None,
    face_image=None,
):
    attendance_date = attendance_date.strip()
    attendance_time = attendance_time.strip()
    student_name = student_name.strip()
    status = status.strip()

    if not attendance_date:
        raise ValueError("Attendance date cannot be empty.")

    if not attendance_time:
        raise ValueError("Attendance time cannot be empty.")

    if not student_name:
        raise ValueError("Student name cannot be empty.")

    if not status:
        raise ValueError("Attendance status cannot be empty.")

    # CRITICAL: Weekend and Holiday attendance restriction check
    allowed, block_msg, _ = check_attendance_allowed(attendance_date)
    if not allowed:
        raise ValueError(block_msg)

    with get_connection() as connection:

        # Fast duplicate check first (indexed on student_id and attendance_date)
        existing_attendance = connection.execute(
            """
            SELECT id
            FROM attendance
            WHERE student_id = ?
              AND attendance_date = ?
            """,
            (student_id, attendance_date),
        ).fetchone()

        if existing_attendance:
            return False

        connection.execute(
            """
            INSERT INTO attendance (
                session_id,
                student_id,
                student_name,
                attendance_date,
                attendance_time,
                status,
                verification_score,
                face_image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                student_id,
                student_name,
                attendance_date,
                attendance_time,
                status,
                verification_score,
                face_image,
            ),
        )

        connection.commit()

    log_activity(
        "ATTENDANCE_MARKED",
        f"Attendance verified for {student_name} ({student_id}) - {status}",
        "attendance",
        student_id
    )

    return True


def get_attendance(attendance_id):
    with get_connection() as connection:
        attendance = connection.execute(
            """
            SELECT
                id,
                session_id,
                student_id,
                student_name,
                attendance_date,
                attendance_time,
                status,
                verification_score,
                face_image
            FROM attendance
            WHERE id = ?
            """,
            (attendance_id,),
        ).fetchone()

    if attendance is None:
        return None

    return dict(attendance)


def get_attendance_by_session(session_id):
    with get_connection() as connection:
        attendance = connection.execute(
            """
            SELECT
                id,
                session_id,
                student_id,
                student_name,
                attendance_date,
                attendance_time,
                status,
                verification_score,
                face_image
            FROM attendance
            WHERE session_id = ?
            ORDER BY attendance_time
            """,
            (session_id,),
        ).fetchall()

    return [dict(record) for record in attendance]


def get_attendance_by_student(student_id):
    with get_connection() as connection:
        attendance = connection.execute(
            """
            SELECT
                id,
                session_id,
                student_id,
                student_name,
                attendance_date,
                attendance_time,
                status,
                verification_score,
                face_image
            FROM attendance
            WHERE student_id = ?
            ORDER BY attendance_date DESC, attendance_time DESC
            """,
            (student_id,),
        ).fetchall()

    return [dict(record) for record in attendance]


def get_attendance_by_date(attendance_date):
    with get_connection() as connection:
        attendance = connection.execute(
            """
            SELECT
                id,
                session_id,
                student_id,
                student_name,
                attendance_date,
                attendance_time,
                status,
                verification_score,
                face_image
            FROM attendance
            WHERE attendance_date = ?
            ORDER BY attendance_time
            """,
            (attendance_date,),
        ).fetchall()

    return [dict(record) for record in attendance]


def update_attendance(
    attendance_id,
    status=None,
    verification_score=None,
):
    with get_connection() as connection:

        existing_attendance = connection.execute(
            """
            SELECT id
            FROM attendance
            WHERE id = ?
            """,
            (attendance_id,),
        ).fetchone()

        if existing_attendance is None:
            return False

        updates = []
        values = []

        if status is not None:
            status = status.strip()

            if not status:
                raise ValueError("Attendance status cannot be empty.")

            updates.append("status = ?")
            values.append(status)

        if verification_score is not None:
            updates.append("verification_score = ?")
            values.append(verification_score)

        if not updates:
            return True

        values.append(attendance_id)

        connection.execute(
            f"""
            UPDATE attendance
            SET {", ".join(updates)}
            WHERE id = ?
            """,
            values,
        )

        connection.commit()

    return True


def attendance_exists(attendance_id):
    with get_connection() as connection:
        attendance = connection.execute(
            """
            SELECT id
            FROM attendance
            WHERE id = ?
            """,
            (attendance_id,),
        ).fetchone()

    return attendance is not None