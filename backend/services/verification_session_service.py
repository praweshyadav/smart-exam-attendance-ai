import base64
from uuid import uuid4
import cv2

from backend.core.config import LIVENESS_ENABLED
from backend.services.verification_service import VerificationService


class VerificationSessionService:
    """
    Manages stateful face verification sessions with per-session
    anti-spoofing, randomized challenge-response liveness, and ownership checks.
    """

    def __init__(self):
        self.sessions = {}

    def create_session(
        self,
        attendance_session_id=None,
        owner_username: str | None = None,
        owner_role: str | None = None,
        expected_student_id: str | None = None,
    ):
        verification_session_id = str(uuid4())

        self.sessions[verification_session_id] = {
            "verification_service": VerificationService(require_liveness=LIVENESS_ENABLED),
            "attendance_session_id": attendance_session_id,
            "owner_username": owner_username,
            "owner_role": owner_role,
            "expected_student_id": expected_student_id,
            "latest_verification": None,
            "completed": False,
        }

        return verification_session_id

    def get_session_meta(self, session_id):
        if session_id not in self.sessions:
            raise ValueError("Verification session does not exist.")
        s = self.sessions[session_id]
        return {
            "attendance_session_id": s["attendance_session_id"],
            "owner_username": s["owner_username"],
            "owner_role": s["owner_role"],
            "expected_student_id": s["expected_student_id"],
            "completed": s["completed"],
        }

    def get_challenge_info(self, session_id):
        if session_id not in self.sessions:
            raise ValueError("Verification session does not exist.")
        ls = self.sessions[session_id]["verification_service"].liveness_service
        if hasattr(ls, "get_challenge_info"):
            return ls.get_challenge_info()
        return None

    def process_frame(self, session_id, frame):
        if session_id not in self.sessions:
            raise ValueError("Verification session does not exist.")

        if frame is None:
            raise ValueError("Frame cannot be None.")

        session = self.sessions[session_id]
        verification_service = session["verification_service"]
        result = verification_service.verify_frame(
            frame,
            expected_student_id=session.get("expected_student_id"),
        )

        # Attach face crop thumbnails for all verified faces in results
        h, w = frame.shape[:2]
        for f_item in result.get("results", [result]):
            f_bbox = f_item.get("bbox")
            if f_bbox and len(f_bbox) >= 4 and f_item.get("verified"):
                try:
                    x1, y1, x2, y2 = f_bbox
                    m = int(0.18 * max(x2 - x1, y2 - y1))
                    crop = frame[max(0, y1 - m):min(h, y2 + m), max(0, x1 - m):min(w, x2 + m)]
                    ok, buf = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                    if ok:
                        b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")
                        f_item["face_image"] = b64
                        if f_item == result or f_item.get("student_id") == result.get("student_id"):
                            result["face_image"] = b64
                except Exception:
                    pass

        session["latest_verification"] = result
        return result

    def get_latest_verification(self, session_id):
        if session_id not in self.sessions:
            raise ValueError("Verification session does not exist.")
        return self.sessions[session_id]["latest_verification"]

    def get_attendance_session_id(self, session_id):
        if session_id not in self.sessions:
            raise ValueError("Verification session does not exist.")
        return self.sessions[session_id]["attendance_session_id"]

    def mark_completed(self, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]["completed"] = True

    def is_completed(self, session_id):
        if session_id not in self.sessions:
            raise ValueError("Verification session does not exist.")
        return bool(self.sessions[session_id].get("completed"))

    def reset_session(self, session_id):
        if session_id not in self.sessions:
            raise ValueError("Verification session does not exist.")

        self.sessions[session_id]["verification_service"].reset_liveness()
        self.sessions[session_id]["latest_verification"] = None
        self.sessions[session_id]["completed"] = False

    def close_session(self, session_id):
        if session_id not in self.sessions:
            return False

        session = self.sessions.pop(session_id)
        session["verification_service"].close()
        return True

    def session_exists(self, session_id):
        return session_id in self.sessions

    def get_session_count(self):
        return len(self.sessions)

    def close_all_sessions(self):
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            self.close_session(session_id)
