from backend.database.database import get_connection


def _calculate_summary(total_records, present_count, late_count, absent_count):
    attended_count = present_count + late_count

    if total_records == 0:
        attendance_percentage = 0.0
    else:
        attendance_percentage = round(
            (attended_count / total_records) * 100,
            2,
        )

    return {
        "total_records": total_records,
        "present_count": present_count,
        "late_count": late_count,
        "absent_count": absent_count,
        "attendance_percentage": attendance_percentage,
    }


def get_overall_attendance():
    """
    Calculate overall attendance using exam rosters.

    Each rostered student in each exam represents one expected
    attendance record.

    The latest attendance session for each exam is used to avoid
    counting the same exam multiple times when an exam has multiple
    attendance sessions.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                r.exam_id,
                r.student_id,
                a.status
            FROM exam_roster r

            LEFT JOIN (
                SELECT
                    a1.student_id,
                    a1.status,
                    s1.exam_id
                FROM attendance a1
                INNER JOIN attendance_sessions s1
                    ON a1.session_id = s1.session_id
                INNER JOIN (
                    SELECT
                        exam_id,
                        MAX(session_id) AS latest_session_id
                    FROM attendance_sessions
                    WHERE exam_id IS NOT NULL
                    GROUP BY exam_id
                ) latest
                    ON s1.exam_id = latest.exam_id
                   AND s1.session_id = latest.latest_session_id
            ) a
                ON r.exam_id = a.exam_id
               AND r.student_id = a.student_id
            """
        ).fetchall()

    total_records = len(rows)
    present_count = sum(
        1 for row in rows if row["status"] == "Present"
    )
    late_count = sum(
        1 for row in rows if row["status"] == "Late"
    )
    absent_count = sum(
        1 for row in rows
        if row["status"] is None or row["status"] == "Absent"
    )

    return _calculate_summary(
        total_records,
        present_count,
        late_count,
        absent_count,
    )


def get_student_attendance(student_id):
    """
    Calculate attendance for one student across all exams
    where the student is rostered.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                r.exam_id,
                r.student_id,
                a.status
            FROM exam_roster r

            LEFT JOIN (
                SELECT
                    a1.student_id,
                    a1.status,
                    s1.exam_id
                FROM attendance a1
                INNER JOIN attendance_sessions s1
                    ON a1.session_id = s1.session_id
                INNER JOIN (
                    SELECT
                        exam_id,
                        MAX(session_id) AS latest_session_id
                    FROM attendance_sessions
                    WHERE exam_id IS NOT NULL
                    GROUP BY exam_id
                ) latest
                    ON s1.exam_id = latest.exam_id
                   AND s1.session_id = latest.latest_session_id
            ) a
                ON r.exam_id = a.exam_id
               AND r.student_id = a.student_id

            WHERE r.student_id = ?
            """,
            (student_id,),
        ).fetchall()

    total_records = len(rows)

    if total_records == 0:
        return {
            "student_id": student_id,
            **_calculate_summary(0, 0, 0, 0),
        }

    present_count = sum(
        1 for row in rows if row["status"] == "Present"
    )
    late_count = sum(
        1 for row in rows if row["status"] == "Late"
    )
    absent_count = sum(
        1 for row in rows
        if row["status"] is None or row["status"] == "Absent"
    )

    return {
        "student_id": student_id,
        **_calculate_summary(
            total_records,
            present_count,
            late_count,
            absent_count,
        ),
    }


def get_all_student_attendance():
    """
    Calculate attendance for every student based on exams
    in which they are rostered.
    """
    with get_connection() as connection:
        students = connection.execute(
            """
            SELECT
                student_id,
                student_name
            FROM students
            ORDER BY student_name
            """
        ).fetchall()

    results = []

    for student in students:
        summary = get_student_attendance(student["student_id"])

        results.append(
            {
                "student_id": student["student_id"],
                "student_name": student["student_name"],
                "total_records": summary["total_records"],
                "present_count": summary["present_count"],
                "late_count": summary["late_count"],
                "absent_count": summary["absent_count"],
                "attendance_percentage": summary[
                    "attendance_percentage"
                ],
            }
        )

    return results


def get_class_attendance(class_id):
    """
    Calculate attendance for all rostered students belonging
    to a class.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                r.exam_id,
                r.student_id,
                a.status
            FROM exam_roster r

            INNER JOIN students s
                ON r.student_id = s.student_id

            INNER JOIN exams e
                ON r.exam_id = e.exam_id

            LEFT JOIN (
                SELECT
                    a1.student_id,
                    a1.status,
                    s1.exam_id
                FROM attendance a1
                INNER JOIN attendance_sessions s1
                    ON a1.session_id = s1.session_id
                INNER JOIN (
                    SELECT
                        exam_id,
                        MAX(session_id) AS latest_session_id
                    FROM attendance_sessions
                    WHERE exam_id IS NOT NULL
                    GROUP BY exam_id
                ) latest
                    ON s1.exam_id = latest.exam_id
                   AND s1.session_id = latest.latest_session_id
            ) a
                ON r.exam_id = a.exam_id
               AND r.student_id = a.student_id

            WHERE e.class_id = ?
            """,
            (class_id,),
        ).fetchall()

    total_records = len(rows)
    present_count = sum(
        1 for row in rows if row["status"] == "Present"
    )
    late_count = sum(
        1 for row in rows if row["status"] == "Late"
    )
    absent_count = sum(
        1 for row in rows
        if row["status"] is None or row["status"] == "Absent"
    )

    return {
        "class_id": class_id,
        **_calculate_summary(
            total_records,
            present_count,
            late_count,
            absent_count,
        ),
    }


def get_exam_attendance(exam_id):
    """
    Calculate attendance for an exam.

    Only the latest attendance session for the exam is used.
    This prevents duplicate counting when an exam has multiple
    attendance sessions.
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
            return {
                "exam_id": exam_id,
                **_calculate_summary(0, 0, 0, 0),
            }

        rows = connection.execute(
            """
            SELECT
                r.student_id,
                a.status
            FROM exam_roster r

            LEFT JOIN (
                SELECT
                    a1.student_id,
                    a1.status
                FROM attendance a1
                INNER JOIN attendance_sessions s1
                    ON a1.session_id = s1.session_id
                WHERE s1.session_id = (
                    SELECT MAX(session_id)
                    FROM attendance_sessions
                    WHERE exam_id = ?
                )
            ) a
                ON r.student_id = a.student_id

            WHERE r.exam_id = ?
            """,
            (exam_id, exam_id),
        ).fetchall()

    total_records = len(rows)
    present_count = sum(
        1 for row in rows if row["status"] == "Present"
    )
    late_count = sum(
        1 for row in rows if row["status"] == "Late"
    )
    absent_count = sum(
        1 for row in rows
        if row["status"] is None or row["status"] == "Absent"
    )

    return {
        "exam_id": exam_id,
        **_calculate_summary(
            total_records,
            present_count,
            late_count,
            absent_count,
        ),
    }


def get_daily_attendance(attendance_date):
    """
    Calculate attendance for exams whose exam date matches
    the supplied date.

    The latest session for each exam is used.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                r.exam_id,
                r.student_id,
                a.status
            FROM exam_roster r

            INNER JOIN exams e
                ON r.exam_id = e.exam_id

            LEFT JOIN (
                SELECT
                    a1.student_id,
                    a1.status,
                    s1.exam_id
                FROM attendance a1
                INNER JOIN attendance_sessions s1
                    ON a1.session_id = s1.session_id
                INNER JOIN (
                    SELECT
                        exam_id,
                        MAX(session_id) AS latest_session_id
                    FROM attendance_sessions
                    WHERE exam_id IS NOT NULL
                    GROUP BY exam_id
                ) latest
                    ON s1.exam_id = latest.exam_id
                   AND s1.session_id = latest.latest_session_id
            ) a
                ON r.exam_id = a.exam_id
               AND r.student_id = a.student_id

            WHERE e.exam_date = ?
            """,
            (attendance_date,),
        ).fetchall()

    total_records = len(rows)
    present_count = sum(
        1 for row in rows if row["status"] == "Present"
    )
    late_count = sum(
        1 for row in rows if row["status"] == "Late"
    )
    absent_count = sum(
        1 for row in rows
        if row["status"] is None or row["status"] == "Absent"
    )

    return {
        "attendance_date": attendance_date,
        **_calculate_summary(
            total_records,
            present_count,
            late_count,
            absent_count,
        ),
    }


def get_attendance_by_date_range(start_date, end_date):
    """
    Calculate daily attendance summaries for a date range.
    """
    with get_connection() as connection:
        dates = connection.execute(
            """
            SELECT DISTINCT exam_date
            FROM exams
            WHERE exam_date BETWEEN ? AND ?
            ORDER BY exam_date
            """,
            (start_date, end_date),
        ).fetchall()

    return [
        get_daily_attendance(row["exam_date"])
        for row in dates
    ]