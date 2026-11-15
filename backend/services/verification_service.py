import inspect
import numpy as np

from backend.ai.face_engine import FaceEngine
from backend.ai.face_matcher import FaceMatcher
from backend.services.challenge_liveness_service import ChallengeLivenessService
from backend.services.student_service import get_student_with_class


class VerificationService:
    """
    Combines face recognition, passive anti-spoofing, and active challenge-response
    liveness detection to verify a student's genuine live presence.
    """

    def __init__(
        self,
        face_engine=None,
        face_matcher=None,
        liveness_service=None,
        require_liveness=True,
        blink_only=True,
    ):
        self.face_engine = face_engine or FaceEngine()
        self.face_matcher = face_matcher or FaceMatcher()
        self.liveness_service = liveness_service or ChallengeLivenessService(blink_only=blink_only)
        self.require_liveness = require_liveness

    def _run_liveness(self, frame, bbox=None, embedding=None):
        """Invoke liveness service with optional bbox/embedding while keeping legacy mocks compatible."""
        sig = inspect.signature(self.liveness_service.process_frame)
        if "face_bbox" in sig.parameters or "face_embedding" in sig.parameters:
            return self.liveness_service.process_frame(
                frame,
                face_bbox=bbox,
                face_embedding=embedding,
            )
        return self.liveness_service.process_frame(frame)

    def verify_frame(self, frame, expected_student_id: str | None = None):
        """
        Verify a student from a webcam frame with mandatory anti-spoof & liveness check.
        """
        if frame is None:
            raise ValueError("Frame cannot be None.")

        faces = self.face_engine.detect_faces(frame)
        h, w = frame.shape[:2] if hasattr(frame, "shape") else (480, 640)

        # Filter valid faces: sensitive threshold to capture multiple students even from distances
        valid_faces = []
        if faces:
            for f in faces:
                score = getattr(f, "det_score", 1.0)
                if score is not None and score < 0.40:
                    continue
                if hasattr(f, "bbox") and f.bbox is not None:
                    x1, y1, x2, y2 = f.bbox
                    if (x2 - x1) < 28 or (y2 - y1) < 28:
                        continue
                valid_faces.append(f)

        if not valid_faces:
            return {
                "verified": False,
                "student_id": None,
                "similarity": None,
                "face_detected": False,
                "face_matched": False,
                "liveness_verified": False,
                "spoof_detected": False,
                "blink_detected": False,
                "blink_count": 0,
                "left_ear": None,
                "right_ear": None,
                "faces_count": 0,
                "results": [],
                "challenge": self.liveness_service.get_challenge_info()
                if hasattr(self.liveness_service, "get_challenge_info")
                else None,
                "reason": "No face detected.",
                "frame_width": w,
                "frame_height": h,
            }

        valid_faces.sort(
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
            if hasattr(f, "bbox") and f.bbox is not None
            else 0,
            reverse=True,
        )

        results = []
        is_multi_face = len(valid_faces) > 1

        for face in valid_faces:
            bbox = face.bbox.astype(int).tolist() if hasattr(face, "bbox") and face.bbox is not None else None
            embedding = self.face_engine.get_embedding(face)
            if embedding is not None:
                embedding = np.asarray(embedding, dtype=np.float32)
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm

            match_result = self.face_matcher.find_best_match(embedding)
            sim = match_result.get("similarity")
            matched = bool(match_result.get("matched", False))
            sid = match_result.get("student_id")

            # Student role ownership restriction: logged-in student can only verify themselves
            if expected_student_id is not None and sid and str(sid) != str(expected_student_id):
                matched = False
                sid = None

            # Anti-spoofing & liveness verification per face
            spoof_detected = False
            liveness_verified = True
            liveness_reason = None
            blink_detected = False
            blink_count = 0
            left_ear = None
            right_ear = None

            if self.require_liveness and not is_multi_face:
                # Single face: execute full interactive challenge-response and passive anti-spoof
                liveness_res = self._run_liveness(frame, bbox=bbox, embedding=embedding)
                liveness_verified = bool(liveness_res.get("liveness_verified", False))
                spoof_detected = bool(liveness_res.get("spoof_detected", False))
                liveness_reason = liveness_res.get("reason")
                blink_detected = liveness_res.get("blink_detected", False)
                blink_count = liveness_res.get("blink_count", 0)
                left_ear = liveness_res.get("left_ear")
                right_ear = liveness_res.get("right_ear")
            elif self.require_liveness and is_multi_face:
                # Multi-face classroom / exam hall mode:
                # Verify passive anti-spoof texture and reflection per face crop to block held screens/photos
                try:
                    from backend.ai.anti_spoof import AntiSpoofDetector
                    if not hasattr(self, "_anti_spoof_detector"):
                        self._anti_spoof_detector = AntiSpoofDetector()
                    sc = self._anti_spoof_detector.analyze_static_cues(frame, bbox=bbox)
                    spoof_detected = bool(sc.get("is_spoof", False))
                    liveness_verified = not spoof_detected
                    if spoof_detected:
                        liveness_reason = sc["reasons"][0] if sc.get("reasons") else "Photo spoof detected."
                except Exception:
                    spoof_detected = False
                    liveness_verified = True

            verified = bool(matched and liveness_verified and not spoof_detected)
            st_info = (get_student_with_class(sid) if sid else None) or {}

            if verified:
                reason = "Student verified successfully with genuine live face."
            elif spoof_detected:
                reason = liveness_reason or "Spoof attack detected. Present your genuine live face."
            elif matched:
                if not blink_detected and not liveness_verified:
                    reason = "Face matched. Please blink your eyes 👁️"
                else:
                    reason = liveness_reason or "Face matched. Completing live verification..."
            else:
                sim_str = f" (similarity: {sim:.2f})" if sim is not None else ""
                reason = f"Face not recognized{sim_str}. Student is not registered."

            item = {
                "verified": verified,
                "matched": matched,
                "student_id": sid,
                "student_name": st_info.get("student_name") or sid,
                "class_name": st_info.get("class_name"),
                "department": st_info.get("department"),
                "semester": st_info.get("semester"),
                "similarity": sim,
                "bbox": bbox,
                "face_detected": True,
                "face_matched": matched,
                "liveness_verified": liveness_verified,
                "spoof_detected": spoof_detected,
                "reason": reason,
                "blink_detected": blink_detected,
                "blink_count": blink_count,
                "left_ear": left_ear,
                "right_ear": right_ear,
            }
            results.append(item)

        # Select primary item: prefer verified face, then matched face, then first face
        primary_item = next((r for r in results if r["verified"]), None)
        if primary_item is None:
            primary_item = next((r for r in results if r["matched"]), results[0])

        challenge_info = (
            self.liveness_service.get_challenge_info()
            if hasattr(self.liveness_service, "get_challenge_info")
            else None
        )

        return {
            **primary_item,
            "faces_count": len(results),
            "results": results,
            "challenge": challenge_info,
            "frame_width": w,
            "frame_height": h,
        }

    def reset_liveness(self):
        if self.liveness_service:
            try:
                self.liveness_service.reset()
            except Exception:
                pass

    def close(self):
        if self.liveness_service:
            try:
                self.liveness_service.close()
            except Exception:
                pass
