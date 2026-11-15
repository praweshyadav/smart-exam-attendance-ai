from datetime import date
from backend.database.database import get_connection
from backend.services.holiday_service import check_attendance_allowed
from backend.services.activity_service import log_activity

# In-memory cache for active attendance session lookups
_session_cache = {}


def get_or_create_general_exam(exam_date=None):
    if not exam_date:
        exam_date = date.today().isoformat()
    exam_name = f"General Real-Time Attendance ({exam_date})"

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT exam_id
            FROM exams
            WHERE exam_name = ?
            ORDER BY exam_id DESC
            LIMIT 1
            """,
            (exam_name,)
        ).fetchone()

        if row:
            return row["exam_id"]

        cursor = connection.execute(
            """
            INSERT INTO exams (exam_name, class_id, exam_date)
            VALUES (?, NULL, ?)
            """,
            (exam_name, exam_date)
        )
        connection.commit()
        return cursor.lastrowid


def start_session(exam_id=None, created_by=None):
    today_str = date.today().isoformat()
    # Check weekend and holiday restrictions
    allowed, block_msg, _ = check_attendance_allowed(today_str)
    if not allowed:
        raise ValueError(block_msg)

    with get_connection() as connection:
        if exam_id is None:
            exam_id = get_or_create_general_exam(today_str)
        else:
            existing_exam = connection.execute(
                """
                SELECT exam_id, exam_date
                FROM exams
                WHERE exam_id = ?
                """,
                (exam_id,)
            ).fetchone()

            if existing_exam is None:
                raise ValueError("Exam does not exist.")

            # Also check the exam date if specified
            if existing_exam.get("exam_date"):
                exam_allowed, exam_block_msg, _ = check_attendance_allowed(existing_exam["exam_date"])
                if not exam_allowed:
                    raise ValueError(exam_block_msg)

        cursor = connection.execute(
            """
            INSERT INTO attendance_sessions (exam_id, created_by)
            VALUES (?, ?)
            """,
            (exam_id, created_by)
        )

        connection.commit()
        sess_id = cursor.lastrowid

    log_activity(
        "SESSION_STARTED",
        f"Attendance session #{sess_id} started (Exam ID: {exam_id})",
        "session",
        sess_id
    )

    return sess_id


def get_session(session_id):
    if not session_id:
        return None

    if session_id in _session_cache:
        cached = _session_cache[session_id]
        return cached.copy() if cached else None

    with get_connection() as connection:
        session = connection.execute(
            """
            SELECT
                session_id,
                exam_id,
                started_at,
                ended_at,
                created_by
            FROM attendance_sessions
            WHERE session_id = ?
            """,
            (session_id,)
        ).fetchone()

    if session is None:
        return None

    res = dict(session)
    if res.get("ended_at") is None:
        _session_cache[session_id] = res
    return res.copy()


def get_all_sessions():
    with get_connection() as connection:
        sessions = connection.execute(
            """
            SELECT
                session_id,
                exam_id,
                started_at,
                ended_at
            FROM attendance_sessions
            ORDER BY started_at DESC
            """
        ).fetchall()

    return [dict(session) for session in sessions]


def get_sessions_by_exam(exam_id):
    with get_connection() as connection:
        sessions = connection.execute(
            """
            SELECT
                session_id,
                exam_id,
                started_at,
                ended_at
            FROM attendance_sessions
            WHERE exam_id = ?
            ORDER BY started_at DESC
            """,
            (exam_id,)
        ).fetchall()

    return [dict(session) for session in sessions]


def end_session(session_id):
    with get_connection() as connection:

        existing_session = connection.execute(
            """
            SELECT session_id
            FROM attendance_sessions
            WHERE session_id = ?
            """,
            (session_id,)
        ).fetchone()

        if existing_session is None:
            return False

        connection.execute(
            """
            UPDATE attendance_sessions
            SET ended_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
            """,
            (session_id,)
        )

        connection.commit()

    _session_cache.pop(session_id, None)
    return True


def session_exists(session_id):
    with get_connection() as connection:
        session = connection.execute(
            """
            SELECT session_id
            FROM attendance_sessions
            WHERE session_id = ?
            """,
            (session_id,)
        ).fetchone()

    return session is not None