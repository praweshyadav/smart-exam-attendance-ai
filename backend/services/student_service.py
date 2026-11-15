from backend.database.database import get_connection
from backend.services.activity_service import log_activity
from backend.services.notification_service import create_notification

# Fast thread-safe in-memory cache for high-frequency student lookups during attendance
_student_cache = {}
_student_with_class_cache = {}


def _invalidate_student_cache(student_id=None):
    if student_id:
        _student_cache.pop(student_id, None)
        _student_with_class_cache.pop(student_id, None)
    else:
        _student_cache.clear()
        _student_with_class_cache.clear()


def add_student(student_id, student_name, class_id=None):
    """
    Add a new student to the database.
    """

    student_id = student_id.strip()
    student_name = student_name.strip()

    if not student_id:
        raise ValueError("Student ID cannot be empty.")

    if not student_name:
        raise ValueError("Student name cannot be empty.")

    with get_connection() as connection:
        existing_student = connection.execute(
            """
            SELECT student_id
            FROM students
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()

        if existing_student:
            return False

        connection.execute(
            """
            INSERT INTO students (
                student_id,
                student_name,
                class_id,
                face_registered
            )
            VALUES (?, ?, ?, 0)
            """,
            (student_id, student_name, class_id)
        )

        connection.commit()

    _invalidate_student_cache(student_id)
    log_activity(
        "STUDENT_REGISTERED",
        f"Student registered: {student_name} ({student_id})",
        "student",
        student_id
    )
    create_notification(
        "Student Registered",
        f"New student {student_name} ({student_id}) registered in the system.",
        "info"
    )
    return True


def get_student_with_class(student_id):
    """
    Get one student with class/section, department, semester information.
    Cached in RAM for zero-latency lookups during high-frequency camera loops.
    """
    if not student_id:
        return None

    if student_id in _student_with_class_cache:
        cached = _student_with_class_cache[student_id]
        return cached.copy() if cached else None

    with get_connection() as connection:
        student = connection.execute(
            """
            SELECT
                s.student_id,
                s.student_name,
                s.class_id,
                s.face_registered,
                s.created_at,
                c.class_name,
                c.department,
                c.semester
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.class_id
            WHERE s.student_id = ?
            """,
            (student_id,)
        ).fetchone()

    res = dict(student) if student is not None else None
    _student_with_class_cache[student_id] = res
    return res.copy() if res else None


def get_student(student_id):
    """
    Get one student using Student ID.
    Cached in RAM to prevent repetitive MySQL roundtrips per frame.
    """
    if not student_id:
        return None

    if student_id in _student_cache:
        cached = _student_cache[student_id]
        return cached.copy() if cached else None

    with get_connection() as connection:
        student = connection.execute(
            """
            SELECT
                student_id,
                student_name,
                class_id,
                face_registered,
                face_image,
                created_at
            FROM students
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()

    res = dict(student) if student is not None else None
    if res:
        res.pop("face_embedding", None)
    _student_cache[student_id] = res
    return res.copy() if res else None


def get_all_students():
    """
    Get all students.
    """

    with get_connection() as connection:
        students = connection.execute(
            """
            SELECT
                student_id,
                student_name,
                class_id,
                face_registered,
                face_image,
                created_at
            FROM students
            ORDER BY student_name
            """
        ).fetchall()

    return [dict(student) for student in students]


def update_student(student_id, student_name=None, class_id=None):
    """
    Update student information.
    """

    with get_connection() as connection:

        existing_student = connection.execute(
            """
            SELECT student_id
            FROM students
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()

        if existing_student is None:
            return False

        if student_name is not None:
            student_name = student_name.strip()

            if not student_name:
                raise ValueError("Student name cannot be empty.")

            connection.execute(
                """
                UPDATE students
                SET student_name = ?,
                    class_id = ?
                WHERE student_id = ?
                """,
                (student_name, class_id, student_id)
            )

        elif class_id is not None:
            connection.execute(
                """
                UPDATE students
                SET class_id = ?
                WHERE student_id = ?
                """,
                (class_id, student_id)
            )

        connection.commit()

    _invalidate_student_cache(student_id)
    log_activity(
        "STUDENT_UPDATED",
        f"Student profile updated: {student_id}",
        "student",
        student_id
    )
    return True


def delete_student(student_id):
    """
    Delete a student from the database.
    """

    with get_connection() as connection:

        existing_student = connection.execute(
            """
            SELECT student_id
            FROM students
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()

        if existing_student is None:
            return False

        connection.execute(
            """
            DELETE FROM students
            WHERE student_id = ?
            """,
            (student_id,)
        )

        connection.commit()

    _invalidate_student_cache(student_id)
    log_activity(
        "STUDENT_DELETED",
        f"Student record removed: {student_id}",
        "student",
        student_id
    )
    return True


def student_exists(student_id):
    """
    Check whether a student exists.
    """

    with get_connection() as connection:
        student = connection.execute(
            """
            SELECT student_id
            FROM students
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()

    return student is not None


def set_face_registered(student_id, registered=True, face_image=None):
    """
    Update the student's face-registration status and face photo.
    """

    with get_connection() as connection:

        existing_student = connection.execute(
            """
            SELECT student_id
            FROM students
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()

        if existing_student is None:
            return False

        if face_image is not None:
            connection.execute(
                """
                UPDATE students
                SET face_registered = ?,
                    face_image = ?
                WHERE student_id = ?
                """,
                (1 if registered else 0, face_image, student_id)
            )
        else:
            connection.execute(
                """
                UPDATE students
                SET face_registered = ?
                WHERE student_id = ?
                """,
                (1 if registered else 0, student_id)
            )

        connection.commit()

    _invalidate_student_cache(student_id)
    log_activity(
        "FACE_REGISTERED",
        f"Biometric face registered for student {student_id}",
        "student",
        student_id
    )
    return True