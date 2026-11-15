from backend.database.database import get_connection


def add_student_to_exam(exam_id, student_id):
    """
    Add a student to an exam roster.
    """
    with get_connection() as connection:
        exam = connection.execute(
            """
            SELECT exam_id
            FROM exams
            WHERE exam_id = ?
            """,
            (exam_id,),
        ).fetchone()

        if exam is None:
            raise ValueError("Exam does not exist.")

        student = connection.execute(
            """
            SELECT student_id
            FROM students
            WHERE student_id = ?
            """,
            (student_id,),
        ).fetchone()

        if student is None:
            raise ValueError("Student does not exist.")

        existing = connection.execute(
            """
            SELECT roster_id
            FROM exam_roster
            WHERE exam_id = ?
              AND student_id = ?
            """,
            (exam_id, student_id),
        ).fetchone()

        if existing:
            return False

        connection.execute(
            """
            INSERT INTO exam_roster (
                exam_id,
                student_id
            )
            VALUES (?, ?)
            """,
            (exam_id, student_id),
        )

        connection.commit()

    return True


def remove_student_from_exam(exam_id, student_id):
    """
    Remove a student from an exam roster.
    """
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT roster_id
            FROM exam_roster
            WHERE exam_id = ?
              AND student_id = ?
            """,
            (exam_id, student_id),
        ).fetchone()

        if existing is None:
            return False

        connection.execute(
            """
            DELETE FROM exam_roster
            WHERE exam_id = ?
              AND student_id = ?
            """,
            (exam_id, student_id),
        )

        connection.commit()

    return True


def get_exam_roster(exam_id):
    """
    Return all students assigned to an exam.
    """
    with get_connection() as connection:
        roster = connection.execute(
            """
            SELECT
                r.roster_id,
                r.exam_id,
                r.student_id,
                s.student_name,
                s.class_id,
                r.added_at
            FROM exam_roster r
            INNER JOIN students s
                ON r.student_id = s.student_id
            WHERE r.exam_id = ?
            ORDER BY s.student_name
            """,
            (exam_id,),
        ).fetchall()

    return [dict(record) for record in roster]


def get_student_exams(student_id):
    """
    Return all exams assigned to a student.
    """
    with get_connection() as connection:
        exams = connection.execute(
            """
            SELECT
                r.roster_id,
                r.exam_id,
                r.student_id,
                e.exam_name,
                e.class_id,
                e.exam_date,
                e.start_time,
                r.added_at
            FROM exam_roster r
            INNER JOIN exams e
                ON r.exam_id = e.exam_id
            WHERE r.student_id = ?
            ORDER BY e.exam_date, e.start_time
            """,
            (student_id,),
        ).fetchall()

    return [dict(record) for record in exams]


def is_student_in_exam(exam_id, student_id):
    """
    Check whether a student belongs to an exam roster or matches the exam class.
    If the exam has no roster and no class assigned, or if student has no class set,
    allow student attendance.
    """
    with get_connection() as connection:
        # 1. Direct roster check
        roster = connection.execute(
            """
            SELECT roster_id
            FROM exam_roster
            WHERE exam_id = ?
              AND student_id = ?
            """,
            (exam_id, student_id),
        ).fetchone()

        if roster is not None:
            return True

        # 2. Match by class
        match = connection.execute(
            """
            SELECT 1
            FROM students s
            JOIN exams e ON s.class_id = e.class_id
            WHERE e.exam_id = ? AND s.student_id = ? AND s.class_id IS NOT NULL
            """,
            (exam_id, student_id),
        ).fetchone()

        if match is not None:
            return True

        # 3. Check exam details
        exam = connection.execute(
            "SELECT class_id FROM exams WHERE exam_id = ?",
            (exam_id,),
        ).fetchone()

        if exam is None:
            return False

        # If exam is not bound to a class, check if it has any roster defined
        if exam["class_id"] is None:
            roster_count = connection.execute(
                "SELECT COUNT(*) as count FROM exam_roster WHERE exam_id = ?",
                (exam_id,),
            ).fetchone()
            if roster_count and roster_count["count"] == 0:
                return True

        # If student has no class set yet, associate with this exam's class
        student = connection.execute(
            "SELECT class_id FROM students WHERE student_id = ?",
            (student_id,),
        ).fetchone()
        if student and student["class_id"] is None and exam["class_id"] is not None:
            connection.execute(
                "UPDATE students SET class_id = ? WHERE student_id = ?",
                (exam["class_id"], student_id),
            )
            return True

    return False


def get_exam_roster_count(exam_id):
    """
    Return the number of students assigned to an exam.
    """
    with get_connection() as connection:
        result = connection.execute(
            """
            SELECT COUNT(*) AS roster_count
            FROM exam_roster
            WHERE exam_id = ?
            """,
            (exam_id,),
        ).fetchone()

    return result["roster_count"] if result else 0


def clear_exam_roster(exam_id):
    """
    Remove all students from an exam roster.
    """
    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM exam_roster
            WHERE exam_id = ?
            """,
            (exam_id,),
        )
        connection.commit()

    return True
