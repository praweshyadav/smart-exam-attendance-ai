from backend.database.database import get_connection
from backend.services.activity_service import log_activity
from backend.services.notification_service import create_notification


def add_class(class_name, department=None, semester=None):
    class_name = class_name.strip()

    if not class_name:
        raise ValueError("Class name cannot be empty.")

    with get_connection() as connection:
        existing_class = connection.execute(
            """
            SELECT class_id
            FROM classes
            WHERE class_name = ?
            """,
            (class_name,)
        ).fetchone()

        if existing_class:
            return False

        cursor = connection.execute(
            """
            INSERT INTO classes (
                class_name,
                department,
                semester
            )
            VALUES (?, ?, ?)
            """,
            (class_name, department, semester)
        )

        connection.commit()
        cls_id = cursor.lastrowid

    log_activity(
        "CLASS_CREATED",
        f"Class created: {class_name} ({department or 'General'})",
        "class",
        str(cls_id)
    )
    create_notification(
        "New Class Added",
        f"Class '{class_name}' ({department or 'General'}) was created.",
        "info"
    )

    return True


def get_class(class_id):
    with get_connection() as connection:
        class_data = connection.execute(
            """
            SELECT
                class_id,
                class_name,
                department,
                semester,
                created_at
            FROM classes
            WHERE class_id = ?
            """,
            (class_id,)
        ).fetchone()

    if class_data is None:
        return None

    return dict(class_data)


def get_all_classes():
    with get_connection() as connection:
        classes = connection.execute(
            """
            SELECT
                class_id,
                class_name,
                department,
                semester,
                created_at
            FROM classes
            ORDER BY class_name
            """
        ).fetchall()

    return [dict(class_data) for class_data in classes]


def update_class(
    class_id,
    class_name=None,
    department=None,
    semester=None
):
    with get_connection() as connection:

        existing_class = connection.execute(
            """
            SELECT class_id
            FROM classes
            WHERE class_id = ?
            """,
            (class_id,)
        ).fetchone()

        if existing_class is None:
            return False

        updates = []
        values = []

        if class_name is not None:
            class_name = class_name.strip()

            if not class_name:
                raise ValueError("Class name cannot be empty.")

            updates.append("class_name = ?")
            values.append(class_name)

        if department is not None:
            updates.append("department = ?")
            values.append(department)

        if semester is not None:
            updates.append("semester = ?")
            values.append(semester)

        if not updates:
            return True

        values.append(class_id)

        connection.execute(
            f"""
            UPDATE classes
            SET {", ".join(updates)}
            WHERE class_id = ?
            """,
            values
        )

        connection.commit()

    return True


def delete_class(class_id):
    with get_connection() as connection:

        existing_class = connection.execute(
            """
            SELECT class_id
            FROM classes
            WHERE class_id = ?
            """,
            (class_id,)
        ).fetchone()

        if existing_class is None:
            return False

        connection.execute(
            """
            DELETE FROM classes
            WHERE class_id = ?
            """,
            (class_id,)
        )

        connection.commit()

    return True


def class_exists(class_id):
    with get_connection() as connection:
        class_data = connection.execute(
            """
            SELECT class_id
            FROM classes
            WHERE class_id = ?
            """,
            (class_id,)
        ).fetchone()

    return class_data is not None


def get_students_by_class(class_id):
    with get_connection() as connection:
        students = connection.execute(
            """
            SELECT
                student_id,
                student_name,
                class_id,
                face_registered,
                created_at
            FROM students
            WHERE class_id = ?
            ORDER BY student_name
            """,
            (class_id,)
        ).fetchall()

    return [dict(student) for student in students]