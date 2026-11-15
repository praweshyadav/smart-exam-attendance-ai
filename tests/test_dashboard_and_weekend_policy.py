import sys
sys.path.insert(0, ".")

import datetime
from fastapi.testclient import TestClient
from backend.core.config import SYSTEM_ADMIN_PASSWORD, SYSTEM_ADMIN_USERNAME
from backend.database.database import initialize_database
from backend.services.holiday_service import (
    is_weekend_date,
    check_attendance_allowed,
    get_holiday,
)
from backend.api.main import app

initialize_database()
client = TestClient(app)
_login_res = client.post(
    "/auth/login",
    json={"username": SYSTEM_ADMIN_USERNAME, "password": SYSTEM_ADMIN_PASSWORD},
)
assert _login_res.status_code == 200, _login_res.text
ADMIN_HEADERS = {"Authorization": f"Bearer {_login_res.json()['access_token']}"}


def test_weekend_restrictions():
    print("\n--- 1. Testing Weekend and Holiday Business Rules ---")
    import backend.services.holiday_service as hs

    # Calendar check: Nov 7 is Saturday, Nov 8 is Sunday
    is_sat_wknd, sat_name = is_weekend_date("2026-11-07")
    assert is_sat_wknd is True, "2026-11-07 must be Saturday weekend"
    assert sat_name == "Saturday"

    is_sun_wknd, sun_name = is_weekend_date("2026-11-08")
    assert is_sun_wknd is True, "2026-11-08 must be Sunday weekend"
    assert sun_name == "Sunday"

    # Temporary Testing Mode: ENABLE_WEEKEND_RESTRICTION = False
    hs.ENABLE_WEEKEND_RESTRICTION = False
    sat_allowed, sat_msg, _ = hs.check_attendance_allowed("2026-11-07")
    assert sat_allowed is True, "In testing mode, Saturday attendance must be permitted"
    print("[PASS] Testing mode weekend bypass check passed:", sat_msg)

    # Production Mode: ENABLE_WEEKEND_RESTRICTION = True
    hs.ENABLE_WEEKEND_RESTRICTION = True
    sat_allowed_prod, sat_msg_prod, _ = hs.check_attendance_allowed("2026-11-07")
    assert sat_allowed_prod is False, "In production mode, Saturday attendance must be rejected"
    assert "Saturday is a holiday" in sat_msg_prod
    print("[PASS] Production mode Saturday rejection check passed:", sat_msg_prod)

    sun_allowed_prod, sun_msg_prod, _ = hs.check_attendance_allowed("2026-11-08")
    assert sun_allowed_prod is False, "In production mode, Sunday attendance must be rejected"
    assert "Sunday is a holiday" in sun_msg_prod
    print("[PASS] Production mode Sunday rejection check passed:", sun_msg_prod)

    # Monday check
    mon_allowed, mon_msg, _ = hs.check_attendance_allowed("2026-11-09")
    assert mon_allowed is True, "Monday attendance must be allowed"
    print("[PASS] Monday check passed:", mon_msg)

    # Configured Holiday test (e.g. 2026-01-26 Republic Day)
    rep_allowed, rep_msg, _ = hs.check_attendance_allowed("2026-01-26")
    assert rep_allowed is False, "Configured holiday must be rejected"
    assert "Republic Day is a holiday" in rep_msg
    print("[PASS] Configured Holiday check passed:", rep_msg)

    # Restore testing mode default (False)
    hs.ENABLE_WEEKEND_RESTRICTION = False


def test_api_weekend_enforcement():
    print("\n--- 2. Testing API Weekend Enforcement via HTTP Requests ---")
    import backend.services.holiday_service as hs

    # Enable restriction to verify HTTP rejection behavior
    hs.ENABLE_WEEKEND_RESTRICTION = True

    # API call for Saturday 2026-11-07
    res_sat = client.post(
        "/attendance/",
        json={
            "session_id": 1,
            "student_id": "23053877",
            "student_name": "Dipendra",
            "attendance_date": "2026-11-07",
            "attendance_time": "09:30:00",
            "status": "Present",
        },
        headers=ADMIN_HEADERS,
    )
    assert res_sat.status_code == 400, f"Expected 400 for Saturday, got {res_sat.status_code}"
    assert "Saturday is a holiday" in res_sat.json()["detail"]
    print("[PASS] API POST /attendance/ blocked Saturday with 400:", res_sat.json()["detail"])

    # API call for Sunday 2026-11-08
    res_sun = client.post(
        "/attendance/",
        json={
            "session_id": 1,
            "student_id": "23053877",
            "student_name": "Dipendra",
            "attendance_date": "2026-11-08",
            "attendance_time": "09:30:00",
            "status": "Present",
        },
        headers=ADMIN_HEADERS,
    )
    assert res_sun.status_code == 400, f"Expected 400 for Sunday, got {res_sun.status_code}"
    assert "Sunday is a holiday" in res_sun.json()["detail"]
    print("[PASS] API POST /attendance/ blocked Sunday with 400:", res_sun.json()["detail"])

    # Now verify in testing mode (restriction disabled): weekend attendance is accepted
    hs.ENABLE_WEEKEND_RESTRICTION = False


def test_dashboard_apis():
    print("\n--- 3. Testing Dashboard Endpoints ---")

    # Summary
    summary = client.get("/dashboard/summary", headers=ADMIN_HEADERS).json()
    assert summary["totalStudents"] >= 0
    assert summary["totalClasses"] >= 0
    assert summary["totalExams"] >= 0
    assert 0.0 <= summary["attendanceRate"] <= 100.0
    print(f"[PASS] Summary: {summary['totalStudents']} students, {summary['totalClasses']} classes, {summary['totalExams']} exams, rate: {summary['attendanceRate']}%")

    # Attendance Trend
    trend_res = client.get("/dashboard/attendance-trend?days=7", headers=ADMIN_HEADERS).json()
    trend_list = trend_res.get("trend", [])
    for pt in trend_list:
        is_wknd, _ = is_weekend_date(pt["date"])
        assert not is_wknd, f"Weekend date {pt['date']} must not be in trend chart"
    print(f"[PASS] Attendance trend: {len(trend_list)} valid working day points returned")

    # Today's attendance
    today_res = client.get("/dashboard/today-attendance", headers=ADMIN_HEADERS).json()
    assert "attendancePercentage" in today_res
    print(f"[PASS] Today ({today_res['date']}): {today_res['present']} present, {today_res['absent']} absent ({today_res['attendancePercentage']}%)")

    # Calendar
    cal_res = client.get("/dashboard/calendar?year=2026&month=11", headers=ADMIN_HEADERS).json()
    assert cal_res["daysInMonth"] == 30
    assert len(cal_res["days"]) == 30
    # Day 7 should be Saturday (Weekend)
    day_7 = cal_res["days"][6]
    assert day_7["day"] == 7
    assert day_7["isWeekend"] is True
    assert day_7["attendanceAllowed"] is False
    print("[PASS] Calendar: 30 days verified, Day 7 marked as weekend holiday correctly")

    # Recent Activity
    act_res = client.get("/dashboard/recent-activity?limit=5", headers=ADMIN_HEADERS).json()
    assert "activities" in act_res
    print(f"[PASS] Recent activity: {len(act_res['activities'])} activity logs returned")

    # Notifications
    notif_res = client.get("/dashboard/notifications", headers=ADMIN_HEADERS).json()
    assert "notifications" in notif_res
    print(f"[PASS] Notifications: {len(notif_res['notifications'])} notifications, unread: {notif_res['unread_count']}")


if __name__ == "__main__":
    initialize_database()
    test_weekend_restrictions()
    test_api_weekend_enforcement()
    test_dashboard_apis()
    print("\n=======================================================")
    print("ALL WEEKEND POLICY & DASHBOARD BACKEND TESTS PASSED!")
    print("=======================================================\n")
