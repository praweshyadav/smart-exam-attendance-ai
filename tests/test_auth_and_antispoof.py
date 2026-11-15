import os
import sys
sys.path.insert(0, os.path.abspath("."))

from types import SimpleNamespace
import cv2
import numpy as np
from fastapi.testclient import TestClient

from backend.ai.anti_spoof import AntiSpoofDetector
from backend.ai.eye_landmarks import EyeLandmarks
from backend.api.main import app
from backend.core.config import SYSTEM_ADMIN_PASSWORD, SYSTEM_ADMIN_USERNAME
from backend.database.database import get_connection, initialize_database
from backend.services.challenge_liveness_service import ChallengeLivenessService


initialize_database()
client = TestClient(app)


def _cleanup_test_entities():
    test_usernames = ("ROLL_TEST_901", "ROLL_TEST_902", "admin_test_2", "admin_test_3")
    with get_connection() as conn:
        for uname in test_usernames:
            conn.execute("DELETE FROM users WHERE username = ?", (uname,))
            conn.execute("DELETE FROM attendance WHERE student_id = ?", (uname,))
            conn.execute("DELETE FROM verification_attempts WHERE student_id = ?", (uname,))
            conn.execute("DELETE FROM attendance_sessions WHERE created_by = ?", (uname,))
            conn.execute("DELETE FROM students WHERE student_id = ?", (uname,))
        conn.commit()


def _make_landmarks(
    ear_open=True,
    mouth_open=False,
    nose_x=0.50,
    left_cheek_x=0.38,
    right_cheek_x=0.62,
):
    lm = [SimpleNamespace(x=0.5, y=0.5, z=0.0) for _ in range(478)]
    eye = (
        [[0.0, 0.0], [1.0, 1.0], [3.0, 1.0], [4.0, 0.0], [3.0, -1.0], [1.0, -1.0]]
        if ear_open
        else [[0.0, 0.0], [1.0, 0.05], [3.0, 0.05], [4.0, 0.0], [3.0, -0.05], [1.0, -0.05]]
    )
    for idx, pt in zip(EyeLandmarks.LEFT_EYE_INDICES, eye):
        lm[idx] = SimpleNamespace(x=pt[0], y=pt[1], z=0.0)
    for idx, pt in zip(EyeLandmarks.RIGHT_EYE_INDICES, eye):
        lm[idx] = SimpleNamespace(x=pt[0], y=pt[1], z=0.0)

    lm[234] = SimpleNamespace(x=left_cheek_x, y=0.50, z=0.08)
    lm[454] = SimpleNamespace(x=right_cheek_x, y=0.50, z=0.08)
    lm[1] = SimpleNamespace(x=nose_x, y=0.52, z=-0.04)

    lm[61] = SimpleNamespace(x=0.45, y=0.65, z=0.0)
    lm[291] = SimpleNamespace(x=0.55, y=0.65, z=0.0)
    lm[13] = SimpleNamespace(x=0.50, y=0.64, z=0.0)
    lm[14] = SimpleNamespace(x=0.50, y=(0.70 if mouth_open else 0.645), z=0.0)
    return lm


class ControlledLivenessDetector:
    def __init__(self):
        self.ear_open = True
        self.mouth_open = False
        self.nose_x = 0.50
        self.yaw = 0.0
        self.blink_score = 0.05
        self.jaw_open = 0.05

    def process_frame(self, frame):
        lm = _make_landmarks(
            ear_open=self.ear_open,
            mouth_open=self.mouth_open,
            nose_x=self.nose_x,
        )
        bs = [
            SimpleNamespace(category_name="eyeBlinkLeft", score=self.blink_score),
            SimpleNamespace(category_name="eyeBlinkRight", score=self.blink_score),
            SimpleNamespace(category_name="jawOpen", score=self.jaw_open),
        ]
        rad = np.radians(self.yaw)
        mat = np.array(
            [
                [np.cos(rad), 0.0, np.sin(rad), 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [-np.sin(rad), 0.0, np.cos(rad), 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float32,
        )
        return SimpleNamespace(
            face_landmarks=[lm],
            face_blendshapes=[bs],
            facial_transformation_matrixes=[mat],
        )

    def close(self):
        pass


def _live_noisy_frame(base_img, step_seed):
    rng = np.random.default_rng(step_seed)
    noise = rng.integers(-4, 5, size=base_img.shape, dtype=np.int16)
    shifted = np.clip(base_img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    # Slight realistic webcam micro-translation
    dx = (step_seed % 3) - 1
    dy = ((step_seed + 1) % 3) - 1
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(shifted, M, (shifted.shape[1], shifted.shape[0]), borderMode=cv2.BORDER_REFLECT)


def test_auth_rbac_and_session_lifecycle():
    print("1. Testing unauthenticated access blocking...")
    for path in (
        "/auth/me",
        "/students/",
        "/classes/",
        "/exams/",
        "/attendance/",
        "/dashboard/summary",
        "/analytics/overall",
        "/verification-attempts/",
    ):
        r = client.get(path)
        assert r.status_code == 401, f"Expected 401 on {path}, got {r.status_code}"

    # Unauthenticated POSTs
    assert client.post("/auth/admin/register", json={"username": "x", "full_name": "x", "password": "password123"}).status_code == 401
    assert client.post("/attendance/", json={
        "session_id": 1, "student_id": "23053877", "student_name": "Dipendra",
        "attendance_date": "2026-11-10", "attendance_time": "10:00",
    }).status_code == 401

    print("2. Testing System Admin login & refresh persistence (/auth/me)...")
    res = client.post("/auth/login", json={"username": SYSTEM_ADMIN_USERNAME, "password": SYSTEM_ADMIN_PASSWORD})
    assert res.status_code == 200, res.text
    sysadmin_data = res.json()
    assert sysadmin_data["user"]["role"] == "admin"
    assert sysadmin_data["user"]["is_system_admin"] is True
    sysadmin_headers = {"Authorization": f"Bearer {sysadmin_data['access_token']}"}

    me_res = client.get("/auth/me", headers=sysadmin_headers)
    assert me_res.status_code == 200
    assert me_res.json()["user"]["username"] == SYSTEM_ADMIN_USERNAME

    print("3. Testing student signup (default role='user', unique Roll No.)...")
    s1_res = client.post(
        "/auth/signup",
        json={"username": "ROLL_TEST_901", "full_name": "Student One", "password": "password123"},
    )
    assert s1_res.status_code == 201, s1_res.text
    s1_json = s1_res.json()
    assert s1_json["user"]["role"] == "user"
    assert s1_json["user"]["username"] == "ROLL_TEST_901"
    assert s1_json["user"]["student_id"] == "ROLL_TEST_901"
    s1_headers = {"Authorization": f"Bearer {s1_json['access_token']}"}

    # Duplicate Roll No must be rejected with 409
    dup_res = client.post(
        "/auth/signup",
        json={"username": "ROLL_TEST_901", "full_name": "Duplicate", "password": "password123"},
    )
    assert dup_res.status_code == 409, f"Expected 409 on duplicate roll_no, got {dup_res.status_code}"

    # Create second student for cross-user authorization checks
    s2_res = client.post(
        "/auth/signup",
        json={"username": "ROLL_TEST_902", "full_name": "Student Two", "password": "password123"},
    )
    assert s2_res.status_code == 201, s2_res.text

    print("4. Testing student RBAC restrictions (self-only vs admin-only)...")
    # Student CAN access own profile & own attendance
    assert client.get("/auth/me", headers=s1_headers).status_code == 200
    assert client.get("/classes/", headers=s1_headers).status_code == 200
    assert client.get("/students/ROLL_TEST_901", headers=s1_headers).status_code == 200
    assert client.get("/attendance/my", headers=s1_headers).status_code == 200
    assert client.get("/attendance/student/ROLL_TEST_901", headers=s1_headers).status_code == 200
    assert client.get("/analytics/student/ROLL_TEST_901", headers=s1_headers).status_code == 200

    # Student CANNOT access other students, all attendance, admin endpoints, or manual attendance
    for forbidden_get in (
        "/students/",
        "/students/ROLL_TEST_902",
        "/attendance/",
        "/attendance/student/ROLL_TEST_902",
        "/analytics/overall",
        "/analytics/student/ROLL_TEST_902",
        "/exams/",
        "/dashboard/summary",
        "/verification-attempts/",
        "/auth/users",
        "/auth/admins",
    ):
        r = client.get(forbidden_get, headers=s1_headers)
        assert r.status_code == 403, f"Expected 403 for student GET {forbidden_get}, got {r.status_code}"

    assert client.post(
        "/auth/admin/register",
        json={"username": "hacker_admin", "full_name": "Hacker", "password": "password123"},
        headers=s1_headers,
    ).status_code == 403

    assert client.post(
        "/attendance/",
        json={
            "session_id": 1,
            "student_id": "ROLL_TEST_901",
            "student_name": "Student One",
            "attendance_date": "2026-11-10",
            "attendance_time": "10:00",
        },
        headers=s1_headers,
    ).status_code == 403

    print("5. Testing admin-only admin registration (System Admin -> Admin2 -> Admin3)...")
    a2_res = client.post(
        "/auth/admin/register",
        json={"username": "admin_test_2", "full_name": "Admin Two", "password": "password123"},
        headers=sysadmin_headers,
    )
    assert a2_res.status_code == 201, a2_res.text
    assert a2_res.json()["user"]["role"] == "admin"
    assert a2_res.json()["user"]["is_system_admin"] is False

    a2_login = client.post("/auth/login", json={"username": "admin_test_2", "password": "password123"})
    assert a2_login.status_code == 200
    a2_headers = {"Authorization": f"Bearer {a2_login.json()['access_token']}"}

    a3_res = client.post(
        "/auth/admin/register",
        json={"username": "admin_test_3", "full_name": "Admin Three", "password": "password123"},
        headers=a2_headers,
    )
    assert a3_res.status_code == 201, a3_res.text

    # System admin account cannot be deleted
    sys_id = sysadmin_data["user"]["id"]
    assert client.delete(f"/auth/users/{sys_id}", headers=a2_headers).status_code == 400

    print("6. Testing logout & token invalidation...")
    logout_res = client.post("/auth/logout", headers=s1_headers)
    assert logout_res.status_code == 200
    assert client.get("/auth/me", headers=s1_headers).status_code == 401

    print("   AUTH & RBAC TESTS PASSED")


def test_antispoof_blocks_photos_and_videos():
    print("7. Testing Anti-Spoof blocking of static photos, tilted photos, and screen replays...")
    img = cv2.imread("tests/test_face.jpg")
    assert img is not None

    # Login as system admin and start a session
    login_res = client.post("/auth/login", json={"username": SYSTEM_ADMIN_USERNAME, "password": SYSTEM_ADMIN_PASSWORD})
    admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Ensure weekday date for test session
    sess_res = client.post("/sessions/", headers=admin_headers)
    assert sess_res.status_code == 200, sess_res.text
    session_id = sess_res.json()["session"]["session_id"]

    # 7a. Single photo submitted to /attendance/verify MUST NOT mark attendance
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    photo_bytes = buf.tobytes()

    single_res = client.post(
        "/attendance/verify",
        data={
            "session_id": str(session_id),
            "attendance_date": "2026-11-10",
            "attendance_time": "10:15",
        },
        files={"image": ("photo.jpg", photo_bytes, "image/jpeg")},
        headers=admin_headers,
    )
    assert single_res.status_code == 200, single_res.text
    sdata = single_res.json()
    assert sdata["attendance"]["attendance_marked"] is False, "Single photo MUST NOT mark attendance!"
    assert sdata["verification"]["verified"] is False
    assert sdata["verification"]["liveness_verified"] is False

    # 7b. Repeated identical photo sent to verification session MUST trigger duplicate/static spoof block
    start_res = client.post(f"/attendance/verify/start?session_id={session_id}", headers=admin_headers)
    assert start_res.status_code == 200
    vsid = start_res.json()["verification_session_id"]
    assert start_res.json()["challenge"]["step"] == 1

    # Frame 1
    r1 = client.post(
        f"/attendance/verify/frame?verification_session_id={vsid}",
        files={"image": ("photo.jpg", photo_bytes, "image/jpeg")},
        headers=admin_headers,
    )
    assert r1.status_code == 200
    assert r1.json()["verification"]["verified"] is False

    # Frame 2 (identical photo bytes -> frozen/duplicate spoof!)
    r2 = client.post(
        f"/attendance/verify/frame?verification_session_id={vsid}",
        files={"image": ("photo.jpg", photo_bytes, "image/jpeg")},
        headers=admin_headers,
    )
    assert r2.status_code == 200
    v2 = r2.json()["verification"]
    assert v2["verified"] is False
    assert v2["liveness_verified"] is False
    assert v2["spoof_detected"] is True, f"Expected spoof_detected=True on duplicate photo, got {v2}"

    # Completing session MUST refuse to mark attendance
    comp_res = client.post(
        f"/attendance/verify/complete?verification_session_id={vsid}",
        data={"attendance_date": "2026-11-10", "attendance_time": "10:16"},
        headers=admin_headers,
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["attendance"]["attendance_marked"] is False

    # 7c. Shaken/tilted 2D photo (affine warp across 6 frames) -> MUST fail liveness
    client.post(f"/attendance/verify/reset?verification_session_id={vsid}", headers=admin_headers)
    for angle in (-6, -3, 0, 3, 6, 0):
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        warped = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)
        _, wbuf = cv2.imencode(".jpg", warped)
        rw = client.post(
            f"/attendance/verify/frame?verification_session_id={vsid}",
            files={"image": ("tilted.jpg", wbuf.tobytes(), "image/jpeg")},
            headers=admin_headers,
        )
        assert rw.status_code == 200
        assert rw.json()["verification"]["verified"] is False
        assert rw.json()["verification"]["liveness_verified"] is False

    # 7d. Screen Moire + Bezel simulation -> AntiSpoofDetector MUST flag spoof
    detector = AntiSpoofDetector()
    spoof_img = img.copy()
    h, w = spoof_img.shape[:2]
    # Add high-frequency periodic LCD grid pattern on face + sharp screen bezel
    gx = (18.0 * np.sin(np.linspace(0, 80 * np.pi, w)))[None, :, None]
    gy = (18.0 * np.sin(np.linspace(0, 80 * np.pi, h)))[:, None, None]
    spoof_img = np.clip(spoof_img.astype(np.float32) + gx + gy, 0, 255).astype(np.uint8)
    cv2.rectangle(spoof_img, (20, 20), (w - 20, h - 20), (255, 255, 255), 4)
    cues = detector.analyze_static_cues(spoof_img)
    assert cues["is_spoof"] is True, f"Expected screen moire+bezel to trigger spoof, got {cues}"

    client.post(f"/attendance/verify/close-session?verification_session_id={vsid}", headers=admin_headers)
    client.put(f"/sessions/{session_id}/end", headers=admin_headers)

    print("8. Testing ChallengeLivenessService randomized 2-step flow & wrong-action video rejection...")
    ctrl = ControlledLivenessDetector()
    cls_svc = ChallengeLivenessService(liveness_detector=ctrl)

    # First verify that doing the WRONG action (like a pre-recorded video) does NOT pass Step 1!
    action1 = cls_svc.current_action
    emb = np.ones(512, dtype=np.float32)
    emb /= np.linalg.norm(emb)

    # Send 6 live frames performing the OPPOSITE action
    for step_i in range(6):
        frame = _live_noisy_frame(img, step_i + 1)
        if action1 == "BLINK":
            # Video opens mouth instead of blinking!
            ctrl.mouth_open = (step_i in (2, 3))
            ctrl.jaw_open = 0.6 if ctrl.mouth_open else 0.05
        else:
            # Video blinks instead of turning head / opening mouth!
            ctrl.ear_open = not (step_i in (2, 3))
            ctrl.blink_score = 0.7 if not ctrl.ear_open else 0.05
        res = cls_svc.process_frame(frame, face_embedding=emb)
        assert res["liveness_verified"] is False
        assert cls_svc.current_step_index == 1, "Wrong action must NOT advance challenge!"

    # Reset and execute the ACTUAL dynamic 2-step sequence!
    cls_svc.reset()
    ctrl = ControlledLivenessDetector()
    cls_svc.liveness_detector = ctrl
    frame_idx = 100

    def _perform_current_step():
        nonlocal frame_idx
        act = cls_svc.current_action
        # 1. Neutral baseline
        ctrl.ear_open, ctrl.mouth_open, ctrl.nose_x, ctrl.yaw = True, False, 0.50, 0.0
        ctrl.blink_score, ctrl.jaw_open = 0.05, 0.05
        res = cls_svc.process_frame(_live_noisy_frame(img, frame_idx), face_embedding=emb)
        frame_idx += 1
        # 2. Peak action
        if act == "BLINK":
            ctrl.ear_open = False
            ctrl.blink_score = 0.75
        elif act == "OPEN_MOUTH":
            ctrl.mouth_open = True
            ctrl.jaw_open = 0.65
        elif act == "TURN_LEFT":
            ctrl.nose_x = 0.41  # (0.41-0.38)/0.24 = 0.125 < 0.37
            ctrl.yaw = -18.0
        elif act == "TURN_RIGHT":
            ctrl.nose_x = 0.59  # (0.59-0.38)/0.24 = 0.875 > 0.63
            ctrl.yaw = 18.0
        res = cls_svc.process_frame(_live_noisy_frame(img, frame_idx), face_embedding=emb)
        frame_idx += 1
        # 3. Recovery to neutral
        ctrl.ear_open, ctrl.mouth_open, ctrl.nose_x, ctrl.yaw = True, False, 0.50, 0.0
        ctrl.blink_score, ctrl.jaw_open = 0.05, 0.05
        res = cls_svc.process_frame(_live_noisy_frame(img, frame_idx), face_embedding=emb)
        frame_idx += 1
        return res

    res_step1 = _perform_current_step()
    assert cls_svc.current_step_index == 2, f"Expected advance to Step 2, got {res_step1}"
    assert res_step1["liveness_verified"] is False
    res_step2 = _perform_current_step()
    assert res_step2["liveness_verified"] is True, f"Expected genuine 2-step live face to verify, got {res_step2}"

    # Verify identity swap mid-challenge resets challenge!
    cls_svc.reset()
    _perform_current_step()
    other_emb = -emb
    swap_res = cls_svc.process_frame(_live_noisy_frame(img, frame_idx + 1), face_embedding=other_emb)
    assert swap_res["liveness_verified"] is False
    assert cls_svc.current_step_index == 1

    cls_svc.close()
    print("   ANTI-SPOOF & LIVENESS CHALLENGE TESTS PASSED")


if __name__ == "__main__":
    _cleanup_test_entities()
    try:
        test_auth_rbac_and_session_lifecycle()
        test_antispoof_blocks_photos_and_videos()
        print("\nALL AUTH, RBAC & ANTI-SPOOF TESTS PASSED")
    finally:
        _cleanup_test_entities()
