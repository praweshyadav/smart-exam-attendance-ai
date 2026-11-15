from backend.database.database import get_connection
from backend.services.analytics_service import (
    get_student_attendance,
    get_class_attendance,
    get_exam_attendance,
    get_daily_attendance,
)


def get_student_report(student_id):
    """
    Generate a complete attendance report for one student.
    """

    with get_connection() as connection:
        student = connection.execute(
            """
            SELECT
                student_id,
                student_name,
                class_id,
                face_registered,
                created_at
            FROM students
            WHERE student_id = ?
            """,
            (student_id,),
        ).fetchone()

        if student is None:
            return None

        exams = connection.execute(
            """
            SELECT
                r.exam_id,
                e.exam_name,
                e.exam_date,
                e.start_time,
                e.class_id
            FROM exam_roster r
            INNER JOIN exams e
                ON r.exam_id = e.exam_id
            WHERE r.student_id = ?
            ORDER BY e.exam_date, e.start_time
            """,
            (student_id,),
        ).fetchall()

    attendance = get_student_attendance(student_id)

    return {
        "student": dict(student),
        "attendance_summary": attendance,
        "exams": [dict(exam) for exam in exams],
    }


def get_class_report(class_id):
    """
    Generate a complete attendance report for a class.
    """

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
            (class_id,),
        ).fetchone()

        if class_data is None:
            return None

        students = connection.execute(
            """
            SELECT
                student_id,
                student_name,
                face_registered
            FROM students
            WHERE class_id = ?
            ORDER BY student_name
            """,
            (class_id,),
        ).fetchall()

        exams = connection.execute(
            """
            SELECT
                exam_id,
                exam_name,
                exam_date,
                start_time
            FROM exams
            WHERE class_id = ?
            ORDER BY exam_date, start_time
            """,
            (class_id,),
        ).fetchall()

    attendance = get_class_attendance(class_id)

    student_reports = []

    for student in students:
        student_summary = get_student_attendance(
            student["student_id"]
        )

        student_reports.append(
            {
                "student_id": student["student_id"],
                "student_name": student["student_name"],
                "face_registered": student["face_registered"],
                "attendance": student_summary,
            }
        )

    return {
        "class": dict(class_data),
        "attendance_summary": attendance,
        "students": student_reports,
        "exams": [dict(exam) for exam in exams],
    }


def get_exam_report(exam_id):
    """
    Generate a complete attendance report for an exam.
    """

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
            (exam_id,),
        ).fetchone()

        if exam is None:
            return None

        roster = connection.execute(
            """
            SELECT
                r.student_id,
                s.student_name,
                s.class_id,
                s.face_registered
            FROM exam_roster r
            INNER JOIN students s
                ON r.student_id = s.student_id
            WHERE r.exam_id = ?
            ORDER BY s.student_name
            """,
            (exam_id,),
        ).fetchall()

        latest_session = connection.execute(
            """
            SELECT
                session_id,
                started_at,
                ended_at
            FROM attendance_sessions
            WHERE exam_id = ?
            ORDER BY session_id DESC
            LIMIT 1
            """,
            (exam_id,),
        ).fetchone()

    attendance_records = []

    if latest_session is not None:
        with get_connection() as connection:
            records = connection.execute(
                """
                SELECT
                    student_id,
                    student_name,
                    attendance_date,
                    attendance_time,
                    status,
                    verification_score
                FROM attendance
                WHERE session_id = ?
                ORDER BY attendance_time
                """,
                (latest_session["session_id"],),
            ).fetchall()

        attendance_records = [
            dict(record) for record in records
        ]

    attendance_summary = get_exam_attendance(exam_id)

    return {
        "exam": dict(exam),
        "attendance_summary": attendance_summary,
        "latest_session": (
            dict(latest_session)
            if latest_session is not None
            else None
        ),
        "roster": [dict(student) for student in roster],
        "attendance": attendance_records,
    }


def get_daily_report(attendance_date):
    """
    Generate an attendance report for all exams
    scheduled on a particular date.
    """

    with get_connection() as connection:
        exams = connection.execute(
            """
            SELECT
                exam_id,
                exam_name,
                class_id,
                exam_date,
                start_time
            FROM exams
            WHERE exam_date = ?
            ORDER BY start_time
            """,
            (attendance_date,),
        ).fetchall()

    exam_reports = []

    for exam in exams:
        exam_report = get_exam_report(exam["exam_id"])

        if exam_report is not None:
            exam_reports.append(exam_report)

    summary = get_daily_attendance(attendance_date)

    return {
        "attendance_date": attendance_date,
        "attendance_summary": summary,
        "exams": exam_reports,
    }


def get_attendance_report(start_date, end_date):
    """
    Generate a date-range attendance report.
    """

    with get_connection() as connection:
        exams = connection.execute(
            """
            SELECT
                exam_id,
                exam_name,
                class_id,
                exam_date,
                start_time
            FROM exams
            WHERE exam_date BETWEEN ? AND ?
            ORDER BY exam_date, start_time
            """,
            (start_date, end_date),
        ).fetchall()

    reports = []

    for exam in exams:
        report = get_exam_report(exam["exam_id"])

        if report is not None:
            reports.append(report)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "reports": reports,
    }