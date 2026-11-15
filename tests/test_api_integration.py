import os
import sys
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.core.config import SYSTEM_ADMIN_PASSWORD, SYSTEM_ADMIN_USERNAME
from backend.database.database import initialize_database


initialize_database()
client = TestClient(app)

_login_res = client.post(
    "/auth/login",
    json={"username": SYSTEM_ADMIN_USERNAME, "password": SYSTEM_ADMIN_PASSWORD},
)
assert _login_res.status_code == 200, f"Admin login failed: {_login_res.text}"
ADMIN_HEADERS = {"Authorization": f"Bearer {_login_res.json()['access_token']}"}


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert "message" in data


def test_unauthenticated_access_blocked():
    assert client.get("/students/").status_code == 401
    assert client.get("/attendance/").status_code == 401
    assert client.get("/dashboard/summary").status_code == 401


def test_student_api_is_available():
    response = client.get("/students/", headers=ADMIN_HEADERS)

    assert response.status_code == 200


def test_class_api_is_available():
    response = client.get("/classes/", headers=ADMIN_HEADERS)

    assert response.status_code == 200


def test_exam_api_is_available():
    response = client.get("/exams/", headers=ADMIN_HEADERS)

    assert response.status_code == 200


def test_attendance_sessions_api_is_available():
    response = client.get("/sessions/", headers=ADMIN_HEADERS)

    assert response.status_code == 200


def test_attendance_api_is_available():
    response = client.get("/attendance/", headers=ADMIN_HEADERS)

    assert response.status_code == 200


def test_verification_attempts_api_is_available():
    response = client.get("/verification-attempts/", headers=ADMIN_HEADERS)

    assert response.status_code == 200


def test_exam_roster_api_is_available():
    exams_res = client.get("/exams/", headers=ADMIN_HEADERS).json()
    exams = exams_res.get("exams", [])
    exam_id = exams[0]["exam_id"] if exams else 2
    response = client.get(
        f"/exam-roster/exam/{exam_id}",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200


def test_analytics_overall_api():
    response = client.get("/analytics/overall", headers=ADMIN_HEADERS)

    assert response.status_code == 200

    data = response.json()

    assert "total_records" in data
    assert "present_count" in data
    assert "late_count" in data
    assert "absent_count" in data
    assert "attendance_percentage" in data


def test_analytics_students_api():
    response = client.get("/analytics/students", headers=ADMIN_HEADERS)

    assert response.status_code == 200

    assert isinstance(response.json(), list)


def test_student_analytics_api():
    response = client.get(
        "/analytics/student/TEST_CLASS_STUDENT_001",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert "student_id" in data
    assert "attendance_percentage" in data


def test_class_analytics_api():
    response = client.get("/analytics/class/11", headers=ADMIN_HEADERS)

    assert response.status_code == 200

    data = response.json()

    assert "class_id" in data
    assert "attendance_percentage" in data


def test_exam_analytics_api():
    response = client.get("/analytics/exam/11", headers=ADMIN_HEADERS)

    assert response.status_code == 200

    data = response.json()

    assert "exam_id" in data
    assert "attendance_percentage" in data


def test_daily_analytics_api():
    response = client.get(
        "/analytics/daily/2026-09-16",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert "attendance_date" in data
    assert "attendance_percentage" in data


def test_range_analytics_api():
    response = client.get(
        "/analytics/range",
        params={
            "start_date": "2026-09-01",
            "end_date": "2026-09-30",
        },
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200

    assert isinstance(response.json(), list)


def test_student_csv_export():
    response = client.get(
        "/exports/student/23053877/csv",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


def test_student_excel_export():
    response = client.get(
        "/exports/student/23053877/excel",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert (
        "spreadsheetml"
        in response.headers["content-type"]
    )


def test_student_pdf_export():
    response = client.get(
        "/exports/student/23053877/pdf",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_class_csv_export():
    response = client.get(
        "/exports/class/1/csv",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


def test_class_excel_export():
    response = client.get(
        "/exports/class/1/excel",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert (
        "spreadsheetml"
        in response.headers["content-type"]
    )


def test_class_pdf_export():
    response = client.get(
        "/exports/class/1/pdf",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_exam_csv_export():
    response = client.get(
        "/exports/exam/2/csv",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


def test_exam_excel_export():
    response = client.get(
        "/exports/exam/2/excel",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert (
        "spreadsheetml"
        in response.headers["content-type"]
    )


def test_exam_pdf_export():
    response = client.get(
        "/exports/exam/2/pdf",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_daily_csv_export():
    response = client.get(
        "/exports/daily/2026-09-16/csv",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


def test_daily_excel_export():
    response = client.get(
        "/exports/daily/2026-09-16/excel",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert (
        "spreadsheetml"
        in response.headers["content-type"]
    )


def test_daily_pdf_export():
    response = client.get(
        "/exports/daily/2026-09-16/pdf",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


if __name__ == '__main__':
    tests = [
        obj for name, obj in list(globals().items())
        if name.startswith('test_') and callable(obj)
    ]
    print(f'Running {len(tests)} API integration tests...')
    for test in tests:
        test()
        print(f'  {test.__name__} PASSED')
    print(f'ALL {len(tests)} API INTEGRATION TESTS PASSED')
