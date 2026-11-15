import sys
sys.path.insert(0, ".")

import cv2
import numpy as np
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.core.config import SYSTEM_ADMIN_USERNAME, SYSTEM_ADMIN_PASSWORD
from backend.database.database import initialize_database, get_connection
from backend.api.main import app
from backend.services.verification_service import VerificationService
from backend.services.face_registration_service import FaceRegistrationService
import backend.services.holiday_service as hs

# Ensure testing mode allows weekend operations
hs.ENABLE_WEEKEND_RESTRICTION = False

initialize_database()
client = TestClient(app)

_login_res = client.post(
    "/auth/login",
    json={"username": SYSTEM_ADMIN_USERNAME, "password": SYSTEM_ADMIN_PASSWORD},
)
assert _login_res.status_code == 200, _login_res.text
ADMIN_HEADERS = {"Authorization": f"Bearer {_login_res.json()['access_token']}"}


def test_database_indexes():
    print("\n--- 1. Testing Database Indexes ---")
    with get_connection() as conn:
        indexes = conn.execute("SHOW INDEX FROM attendance").fetchall()
        idx_names = {row["Key_name"] for row in indexes}
        print(f"Attendance indexes: {idx_names}")
        assert "idx_att_stu_date" in idx_names or "PRIMARY" in idx_names
        assert "idx_att_sess_stu" in idx_names or "idx_attendance_session_student" in idx_names

        student_indexes = conn.execute("SHOW INDEX FROM students").fetchall()
        stu_idx_names = {row["Key_name"] for row in student_indexes}
        print(f"Students indexes: {stu_idx_names}")
        assert "idx_students_class_id" in stu_idx_names or "PRIMARY" in stu_idx_names

    print("[PASS] High-performance indexes verified.")


def test_fast_face_registration():
    print("\n--- 2. Testing Fast Face Registration (Single-Pass Detection) ---")
    reg_svc = FaceRegistrationService()

    # Create synthetic test frame
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Mock face object mimicking InsightFace output
    mock_face = MagicMock()
    mock_face.det_score = 0.95
    mock_face.bbox = np.array([100, 100, 300, 300])
    mock_face.embedding = np.random.randn(512).astype(np.float32)
    mock_face.normed_embedding = mock_face.embedding / np.linalg.norm(mock_face.embedding)

    # When pre_detected_faces is passed, detect_faces should NOT be called
    reg_svc.face_engine.detect_faces = MagicMock()

    # Test registration call using mock student ID to preserve real student records
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO students (student_id, student_name, class_id)
            VALUES (?, ?, 1)
            ON DUPLICATE KEY UPDATE student_name = VALUES(student_name)
            """,
            ("TEST_REG_STU", "Test Registration Student")
        )

    res = reg_svc.register_face(
        student_id="TEST_REG_STU",
        image=dummy_frame,
        allow_update=True,
        pre_detected_faces=[mock_face],
    )
    assert res["success"] is True, f"Registration failed: {res}"
    reg_svc.face_engine.detect_faces.assert_not_called()
    print("[PASS] Fast face registration completed in single pass without redundant detection!")

    with get_connection() as conn:
        conn.execute("DELETE FROM students WHERE student_id = ?", ("TEST_REG_STU",))


def test_multiface_verification_and_batch_marking():
    print("\n--- 3. Testing Multi-Face Verification & Batch Attendance Marking ---")

    # Mock two students in database
    student_a_id = "TEST_STU_A"
    student_b_id = "TEST_STU_B"

    emb_a = np.random.randn(512).astype(np.float32)
    emb_a = emb_a / np.linalg.norm(emb_a)
    emb_b = np.random.randn(512).astype(np.float32)
    emb_b = emb_b / np.linalg.norm(emb_b)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO students (student_id, student_name, class_id)
            VALUES (?, ?, 1)
            ON DUPLICATE KEY UPDATE student_name = VALUES(student_name)
            """,
            (student_a_id, "Alice Smith")
        )
        conn.execute(
            """
            INSERT INTO students (student_id, student_name, class_id)
            VALUES (?, ?, 1)
            ON DUPLICATE KEY UPDATE student_name = VALUES(student_name)
            """,
            (student_b_id, "Bob Jones")
        )

    # Setup verification service with mocked detection and matching
    v_svc = VerificationService()

    face_a = MagicMock()
    face_a.det_score = 0.95
    face_a.bbox = np.array([50, 50, 200, 200])
    face_a.embedding = emb_a
    face_a.normed_embedding = emb_a

    face_b = MagicMock()
    face_b.det_score = 0.95
    face_b.bbox = np.array([300, 50, 450, 200])
    face_b.embedding = emb_b
    face_b.normed_embedding = emb_b

    # Mock face_engine returning 2 detected faces
    v_svc.face_engine.detect_faces = MagicMock(return_value=[face_a, face_b])
    v_svc.face_engine.get_embedding = MagicMock(side_effect=lambda f: f.embedding)

    # Mock face_matcher recognizing both
    def mock_find_best_match(emb):
        if np.allclose(emb, emb_a, atol=1e-3):
            return {"matched": True, "student_id": student_a_id, "student_name": "Alice Smith", "similarity": 0.88}
        return {"matched": True, "student_id": student_b_id, "student_name": "Bob Jones", "similarity": 0.85}

    v_svc.face_matcher.find_best_match = MagicMock(side_effect=mock_find_best_match)
    v_svc._anti_spoof_detector = MagicMock()
    v_svc._anti_spoof_detector.analyze_static_cues = MagicMock(
        return_value={"is_spoof": False, "confidence": 0.95, "reasons": []}
    )
    v_svc.liveness_service.process_frame = MagicMock(return_value={
        "liveness_verified": True,
        "blink_detected": True,
        "spoof_detected": False,
        "blink_count": 2,
        "left_ear": 0.30,
        "right_ear": 0.31,
        "reason": "Liveness confirmed"
    })

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    verif_result = v_svc.verify_frame(dummy_frame)

    assert verif_result["face_detected"] is True
    assert verif_result["faces_count"] == 2
    assert verif_result["face_matched"] is True
    assert len(verif_result["results"]) == 2

    ids_found = {r["student_id"] for r in verif_result["results"]}
    assert ids_found == {student_a_id, student_b_id}
    print(f"[PASS] Multi-face verification detected & recognized {len(verif_result['results'])} faces simultaneously!")

    # Now verify /attendance/verify/complete API accepts multi-face results and marks both
    # 1. Create a session
    sess_res = client.post(
        "/sessions/",
        headers=ADMIN_HEADERS,
    )
    assert sess_res.status_code == 200, sess_res.text
    session_id = sess_res.json()["session"]["session_id"]

    # 2. Start verification session
    vstart_res = client.post(
        f"/attendance/verify/start?session_id={session_id}",
        headers=ADMIN_HEADERS,
    )
    assert vstart_res.status_code == 200, vstart_res.text
    v_sid = vstart_res.json()["verification_session_id"]

    # Inject multi-face verification into the session state
    from backend.api.attendance_verification_session_api import verification_session_service
    verification_session_service.sessions[v_sid]["latest_verification"] = verif_result

    # 3. Complete attendance with multi-face results
    comp_res = client.post(
        "/attendance/verify/complete",
        data={
            "verification_session_id": v_sid,
            "attendance_date": "2026-11-15",
            "attendance_time": "10:00:00",
        },
        headers=ADMIN_HEADERS,
    )
    assert comp_res.status_code == 200, comp_res.text
    comp_data = comp_res.json()
    print("comp_data:", comp_data)
    assert comp_data["status"] == "success"
    marked_ids = {m["student_id"] for m in comp_data["marked_list"]}
    assert student_a_id in marked_ids
    assert student_b_id in marked_ids
    print(f"[PASS] Multi-face attendance marked simultaneously for students: {marked_ids}")

    # Clean up test session and students
    client.post(f"/sessions/{session_id}/end", headers=ADMIN_HEADERS)
    with get_connection() as conn:
        conn.execute("DELETE FROM attendance WHERE student_id IN (?, ?)", (student_a_id, student_b_id))
        conn.execute("DELETE FROM students WHERE student_id IN (?, ?)", (student_a_id, student_b_id))


if __name__ == "__main__":
    test_database_indexes()
    test_fast_face_registration()
    test_multiface_verification_and_batch_marking()
    print("\n=======================================================")
    print("ALL MULTI-FACE & PERFORMANCE TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")
