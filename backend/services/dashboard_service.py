import datetime
import calendar
from backend.database.database import get_connection
from backend.services.holiday_service import (
    is_weekend_date,
    get_holiday,
    check_attendance_allowed,
    get_holidays_for_month,
)
from backend.services.activity_service import get_recent_activities
from backend.services.notification_service import (
    get_notifications,
    mark_notification_read,
    mark_all_notifications_read,
)


def get_dashboard_summary():
    """
    Returns high-level statistics for the 4 StatCards:
    - Total Students (actual count)
    - Total Classes (actual count)
    - Total Exams (actual count)
    - Attendance Rate (calculated strictly on working days with attendance sessions)
    """
    today_str = datetime.date.today().isoformat()

    with get_connection() as connection:
        total_students = connection.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
        total_classes = connection.execute("SELECT COUNT(*) AS c FROM classes").fetchone()["c"]
        total_exams = connection.execute("SELECT COUNT(*) AS c FROM exams").fetchone()["c"]

        # Calculate overall attendance rate across valid working days
        # Group by attendance_date to find present count per day
        att_rows = connection.execute(
            """
            SELECT attendance_date, COUNT(DISTINCT student_id) AS present_count
            FROM attendance
            WHERE status = 'Present'
            GROUP BY attendance_date
            ORDER BY attendance_date ASC
            """
        ).fetchall()

    total_present_instances = 0
    total_eligible_instances = 0

    for row in att_rows:
        adate = row["attendance_date"]
        # Skip weekends and holidays from calculation
        is_wknd, _ = is_weekend_date(adate)
        if is_wknd or get_holiday(adate):
            continue

        p_cnt = row["present_count"]
        # Eligible students count: use total students in system (or rostered if any)
        total_present_instances += p_cnt
        total_eligible_instances += max(total_students, p_cnt)

    if total_eligible_instances > 0:
        attendance_rate = round((total_present_instances / total_eligible_instances) * 100, 1)
    else:
        attendance_rate = 0.0

    return {
        "totalStudents": total_students,
        "totalClasses": total_classes,
        "totalExams": total_exams,
        "attendanceRate": attendance_rate,
        "studentChange": None,  # Neutral indicator when historical comparison unavailable
        "classChange": None,
        "asOf": today_str,
        "admin": {
            "name": "Admin",
            "role": "System Administrator",
            "email": "admin@smartattendance.edu",
        },
    }


def get_attendance_trend(days: int = 7):
    """
    Returns daily attendance trend for the last N days.
    CRITICAL: Excludes Saturday, Sunday, holidays, and days without sessions.
    """
    days = max(7, min(days, 60))
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=days)

    with get_connection() as connection:
        total_students = connection.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]

        rows = connection.execute(
            """
            SELECT attendance_date, COUNT(DISTINCT student_id) AS present_count
            FROM attendance
            WHERE attendance_date BETWEEN ? AND ?
              AND status = 'Present'
            GROUP BY attendance_date
            ORDER BY attendance_date ASC
            """,
            (start_date.isoformat(), today.isoformat())
        ).fetchall()

    trend = []
    for r in rows:
        d_str = r["attendance_date"]
        # Strictly exclude weekends and holidays
        is_wknd, _ = is_weekend_date(d_str)
        if is_wknd or get_holiday(d_str):
            continue

        d_obj = datetime.date.fromisoformat(d_str)
        p_cnt = r["present_count"]
        eligible = max(total_students, p_cnt)
        pct = round((p_cnt / eligible) * 100, 1) if eligible > 0 else 0.0

        trend.append({
            "date": d_str,
            "day": d_obj.strftime("%a"),
            "fullDate": d_obj.strftime("%b %d, %Y"),
            "present": p_cnt,
            "absent": max(0, eligible - p_cnt),
            "totalEligible": eligible,
            "percentage": pct,
        })

    return {
        "days": days,
        "count": len(trend),
        "trend": trend,
    }


def get_today_attendance():
    """
    Returns attendance metrics for today.
    Handles weekend holiday states and public holidays gracefully.
    """
    today = datetime.date.today()
    today_str = today.isoformat()

    is_allowed, block_msg, reason_type = check_attendance_allowed(today_str)
    is_wknd, day_name = is_weekend_date(today_str)
    holiday = get_holiday(today_str)

    if not is_allowed:
        return {
            "date": today_str,
            "isWeekend": is_wknd,
            "isHoliday": bool(holiday),
            "holidayReason": block_msg,
            "attendanceAllowed": False,
            "dayName": day_name,
            "present": 0,
            "absent": 0,
            "totalEligible": 0,
            "attendancePercentage": 0.0,
        }

    with get_connection() as connection:
        total_students = connection.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
        p_row = connection.execute(
            """
            SELECT COUNT(DISTINCT student_id) AS present_count
            FROM attendance
            WHERE attendance_date = ? AND status = 'Present'
            """,
            (today_str,)
        ).fetchone()

    present_count = p_row["present_count"] if p_row else 0
    total_eligible = max(total_students, present_count)
    absent_count = max(0, total_eligible - present_count)
    percentage = round((present_count / total_eligible) * 100, 1) if total_eligible > 0 else 0.0

    return {
        "date": today_str,
        "isWeekend": False,
        "isHoliday": False,
        "holidayReason": None,
        "attendanceAllowed": True,
        "dayName": day_name,
        "present": present_count,
        "absent": absent_count,
        "totalEligible": total_eligible,
        "attendancePercentage": percentage,
    }


def get_calendar_month(year: int = None, month: int = None):
    """
    Generates actual monthly calendar days for given month and year.
    Accurately handles leap years, month lengths (28, 29, 30, 31),
    weekdays, weekends, university holidays, and attendance records.
    """
    today = datetime.date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    # Get number of days in month and starting day of week
    num_days = calendar.monthrange(year, month)[1]

    start_date = f"{year:04d}-{month:02d}-01"
    end_date = f"{year:04d}-{month:02d}-{num_days:02d}"

    with get_connection() as connection:
        total_students = connection.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]

        # Fetch attendance counts for the whole month in one single query
        att_rows = connection.execute(
            """
            SELECT attendance_date, COUNT(DISTINCT student_id) AS present_count
            FROM attendance
            WHERE attendance_date BETWEEN ? AND ?
              AND status = 'Present'
            GROUP BY attendance_date
            """,
            (start_date, end_date)
        ).fetchall()

        # Fetch sessions for this month
        session_rows = connection.execute(
            """
            SELECT DISTINCT DATE(started_at) AS session_date
            FROM attendance_sessions
            WHERE started_at BETWEEN ? AND ?
            """,
            (f"{start_date} 00:00:00", f"{end_date} 23:59:59")
        ).fetchall()

    att_map = {r["attendance_date"]: r["present_count"] for r in att_rows}
    session_dates = {str(r["session_date"]) for r in session_rows if r.get("session_date")}

    # Get holidays for this month
    holidays = get_holidays_for_month(year, month)
    holiday_map = {h["holiday_date"]: h for h in holidays}

    days_data = []
    for day in range(1, num_days + 1):
        cur_date = datetime.date(year, month, day)
        d_str = cur_date.isoformat()
        is_wknd, day_name = is_weekend_date(cur_date)
        h_info = holiday_map.get(d_str)

        has_att = d_str in att_map
        present_cnt = att_map.get(d_str, 0)
        has_sess = (d_str in session_dates) or has_att

        eligible = max(total_students, present_cnt) if has_att else 0
        pct = round((present_cnt / eligible) * 100, 1) if eligible > 0 else None

        days_data.append({
            "day": day,
            "date": d_str,
            "dayOfWeek": (cur_date.weekday() + 1) % 7,  # 0=Sunday, 1=Monday ... 6=Saturday
            "weekdayName": day_name,
            "isWeekend": is_wknd,
            "isHoliday": bool(h_info),
            "holidayName": h_info["holiday_name"] if h_info else None,
            "isToday": (cur_date == today),
            "isPast": (cur_date < today),
            "isFuture": (cur_date > today),
            "attendanceAllowed": not (is_wknd or bool(h_info)),
            "hasSession": has_sess,
            "hasAttendance": has_att,
            "presentCount": present_cnt,
            "totalEligible": eligible,
            "attendancePercentage": pct,
        })

    return {
        "year": year,
        "month": month,
        "monthName": calendar.month_name[month],
        "daysInMonth": num_days,
        "days": days_data,
    }


def global_search(query: str):
    """
    Fast search across Students, Classes, and Exams.
    """
    q = query.strip()
    if not q or len(q) < 2:
        return {"students": [], "classes": [], "exams": []}

    like_pattern = f"%{q}%"

    with get_connection() as connection:
        students = connection.execute(
            """
            SELECT s.student_id, s.student_name, s.face_registered, c.class_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.class_id
            WHERE s.student_id LIKE ? OR s.student_name LIKE ?
            ORDER BY s.student_name ASC
            LIMIT 6
            """,
            (like_pattern, like_pattern)
        ).fetchall()

        classes = connection.execute(
            """
            SELECT class_id, class_name, department, semester
            FROM classes
            WHERE class_name LIKE ? OR department LIKE ?
            ORDER BY class_name ASC
            LIMIT 5
            """,
            (like_pattern, like_pattern)
        ).fetchall()

        exams = connection.execute(
            """
            SELECT exam_id, exam_name, exam_date, start_time
            FROM exams
            WHERE exam_name LIKE ?
            ORDER BY exam_date DESC
            LIMIT 5
            """,
            (like_pattern,)
        ).fetchall()

    return {
        "students": [dict(s) for s in students],
        "classes": [dict(c) for c in classes],
        "exams": [dict(e) for e in exams],
    }
