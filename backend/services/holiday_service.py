import datetime
from backend.core.config import ENABLE_WEEKEND_RESTRICTION
from backend.database.database import get_connection


def parse_date(date_val):
    if isinstance(date_val, datetime.datetime):
        return date_val.date()
    if isinstance(date_val, datetime.date):
        return date_val
    if isinstance(date_val, str):
        # Handle 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
        date_part = date_val.strip().split(" ")[0].split("T")[0]
        return datetime.date.fromisoformat(date_part)
    raise ValueError(f"Invalid date value: {date_val}")


def is_weekend_date(date_val):
    """
    Returns (is_weekend: bool, day_name: str).
    Saturday = 5, Sunday = 6.
    """
    d = parse_date(date_val)
    weekday = d.weekday()  # Monday is 0 and Sunday is 6
    day_name = "Saturday" if weekday == 5 else ("Sunday" if weekday == 6 else d.strftime("%A"))
    return (weekday in (5, 6)), day_name


def get_holiday(date_val):
    """
    Check if the given date is in the holidays database table.
    """
    d_str = parse_date(date_val).isoformat()
    with get_connection() as connection:
        holiday = connection.execute(
            """
            SELECT id, holiday_date, holiday_name, description
            FROM holidays
            WHERE holiday_date = ?
            LIMIT 1
            """,
            (d_str,)
        ).fetchone()
    return dict(holiday) if holiday else None


def check_attendance_allowed(date_val):
    """
    Business check for attendance eligibility on given date.
    NOTE: Weekend restriction is configurable via ENABLE_WEEKEND_RESTRICTION.
    Temporarily disabled to allow testing/verification on any day.

    Returns:
        is_allowed: bool
        message: str
        reason_type: 'weekend' | 'holiday' | None
    """
    if ENABLE_WEEKEND_RESTRICTION:
        is_wknd, day_name = is_weekend_date(date_val)
        if is_wknd:
            return False, f"Attendance cannot be marked on weekends. {day_name} is a holiday.", "weekend"

    holiday = get_holiday(date_val)
    if holiday:
        h_name = holiday.get("holiday_name", "Public Holiday")
        return False, f"Attendance cannot be marked on holidays. {h_name} is a holiday.", "holiday"

    return True, "Attendance marking is permitted.", None


def get_holidays_for_month(year: int, month: int):
    start_date = f"{year:04d}-{month:02d}-01"
    # Find last day of month
    if month == 12:
        end_date = f"{year:04d}-12-31"
    else:
        next_month_first = datetime.date(year, month + 1, 1)
        last_day = (next_month_first - datetime.timedelta(days=1)).day
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, holiday_date, holiday_name, description
            FROM holidays
            WHERE holiday_date BETWEEN ? AND ?
            ORDER BY holiday_date ASC
            """,
            (start_date, end_date)
        ).fetchall()

    return [dict(r) for r in rows]
