import secrets
import time
import numpy as np

from backend.ai.anti_spoof import AntiSpoofDetector
from backend.ai.blink_detector import BlinkDetector
from backend.ai.liveness_detector import LivenessDetector
from backend.core.config import BLINK_THRESHOLD, CHALLENGE_STEP_TIMEOUT_SECONDS


CHALLENGE_META = {
    "BLINK": {
        "title": "Blink Your Eyes",
        "instruction": "Look at the camera and blink both eyes clearly once.",
    },
    "OPEN_MOUTH": {
        "title": "Open & Close Mouth",
        "instruction": "Open your mouth briefly, then close it.",
    },
    "TURN_LEFT": {
        "title": "Turn Head Left",
        "instruction": "Turn your head slightly LEFT, then look straight.",
    },
    "TURN_RIGHT": {
        "title": "Turn Head Right",
        "instruction": "Turn your head slightly RIGHT, then look straight.",
    },
}

ARTICULATION_ACTIONS = ["BLINK", "OPEN_MOUTH"]
POSE_ACTIONS = ["TURN_LEFT", "TURN_RIGHT"]
ALL_ACTIONS = ARTICULATION_ACTIONS + POSE_ACTIONS


class ChallengeLivenessService:
    """
    Stateful anti-spoofing + randomized 2-step active challenge-response liveness verifier.

    Prevents:
    - Static / printed / phone-screen photos (via pixel motion, FFT moire, glare, bezel, and active articulations)
    - Tilted / shaken 2D photos (via mandatory internal muscle articulation BLINK / OPEN_MOUTH)
    - Pre-recorded video replays (via dynamic secret Step 2 chosen only after Step 1 succeeds + strict baseline & timeout)
    - Face swapping mid-verification (via identity embedding continuity across steps)
    """

    def __init__(
        self,
        liveness_detector=None,
        blink_detector=None,
        anti_spoof=None,
        step_timeout_seconds: float = CHALLENGE_STEP_TIMEOUT_SECONDS,
        blink_only: bool = False,
    ):
        self.blink_only = blink_only
        self.liveness_detector = liveness_detector or LivenessDetector()
        self.blink_detector = blink_detector or BlinkDetector(
            blink_threshold=BLINK_THRESHOLD,
            min_closed_frames=1,
        )
        self.anti_spoof = anti_spoof or AntiSpoofDetector()
        self.step_timeout_seconds = step_timeout_seconds
        self.reset()

    def reset(self):
        """Reset state."""
        self.blink_detector.reset()
        self.anti_spoof.reset()
        if getattr(self, "blink_only", False):
            self.current_step_index = 1
            self.total_steps = 1
            self.current_action = "BLINK"
        else:
            self.current_step_index = 1  # 1 or 2
            self.total_steps = 2
            self.current_action = secrets.choice(ALL_ACTIONS)
        self.completed_actions = []
        self.liveness_verified = False

        # Per-step phase tracking: need neutral baseline -> peak action -> recovery
        self._baseline_seen = False
        self._peak_seen = False
        self._step_started_at = time.monotonic()
        self._live_frames_count = 0
        self._spoof_streak = 0
        self._anchor_embedding = None
        self._baseline_nose_ratio = None

    def _pick_next_action(self, first_action: str) -> str:
        """
        Dynamically choose Step 2 AFTER Step 1 completes.
        Guarantees at least one internal muscle articulation (BLINK or OPEN_MOUTH)
        and ensures Step 2 differs from Step 1.
        """
        if first_action in POSE_ACTIONS:
            return secrets.choice(ARTICULATION_ACTIONS)
        candidates = [a for a in ALL_ACTIONS if a != first_action]
        return secrets.choice(candidates)

    def _advance_or_complete(self):
        self.completed_actions.append(self.current_action)
        if self.current_step_index < self.total_steps:
            self.current_step_index += 1
            self.current_action = self._pick_next_action(self.completed_actions[-1])
            self._baseline_seen = False
            self._peak_seen = False
            self._step_started_at = time.monotonic()
        else:
            self.liveness_verified = True

    @staticmethod
    def _extract_blendshapes(results) -> dict[str, float]:
        blendshapes = getattr(results, "face_blendshapes", None)
        if not blendshapes or len(blendshapes) == 0:
            return {}
        return {b.category_name: float(b.score) for b in blendshapes[0]}

    @staticmethod
    def _extract_pose(results, landmarks) -> dict[str, float]:
        yaw = 0.0
        pitch = 0.0
        matrices = getattr(results, "facial_transformation_matrixes", None)
        if matrices and len(matrices) > 0:
            mat = np.asarray(matrices[0], dtype=np.float32)[:3, :3]
            yaw = float(np.degrees(np.arctan2(mat[2, 0], mat[2, 2])))
            pitch = float(np.degrees(np.arcsin(-np.clip(mat[2, 1], -1.0, 1.0))))

        # Nose horizontal ratio between left (234) and right (454) cheek contours
        nose_ratio = 0.5
        if landmarks and len(landmarks) > 454:
            lx = float(landmarks[234].x)
            rx = float(landmarks[454].x)
            nx = float(landmarks[1].x)
            span = rx - lx
            if abs(span) > 1e-4:
                nose_ratio = (nx - lx) / span

        # Mouth Aspect Ratio (MAR) from upper lip (13), lower lip (14), corners (61, 291)
        mar = 0.0
        if landmarks and len(landmarks) > 291:
            mouth_w = float(np.hypot(landmarks[291].x - landmarks[61].x, landmarks[291].y - landmarks[61].y))
            mouth_h = float(np.hypot(landmarks[14].x - landmarks[13].x, landmarks[14].y - landmarks[13].y))
            if mouth_w > 1e-4:
                mar = mouth_h / mouth_w

        return {
            "yaw": yaw,
            "pitch": pitch,
            "nose_ratio": nose_ratio,
            "mar": mar,
        }

    def get_challenge_info(self) -> dict:
        if getattr(self, "blink_only", False):
            return {
                "step": 1,
                "total_steps": 1,
                "action": "BLINK",
                "title": "Blink Eyes",
                "instruction": "Please blink your eyes naturally 👁️",
                "blink_only": True,
                "liveness_verified": self.liveness_verified,
            }
        meta = CHALLENGE_META.get(self.current_action, CHALLENGE_META["BLINK"])
        elapsed = time.monotonic() - self._step_started_at
        remaining = max(0.0, self.step_timeout_seconds - elapsed)
        return {
            "step": self.current_step_index,
            "total_steps": self.total_steps,
            "action": self.current_action,
            "title": meta["title"],
            "instruction": meta["instruction"],
            "completed_actions": list(self.completed_actions),
            "baseline_ready": self._baseline_seen,
            "action_peak_detected": self._peak_seen,
            "remaining_seconds": round(remaining, 1),
            "liveness_verified": self.liveness_verified,
        }

    def process_frame(self, frame, face_bbox=None, face_embedding=None) -> dict:
        if frame is None:
            raise ValueError("Frame cannot be None.")

        # Check challenge step expiration (only in multi-step challenge mode)
        if not getattr(self, "blink_only", False):
            if not self.liveness_verified and (time.monotonic() - self._step_started_at) > self.step_timeout_seconds:
                self.reset()
                return {
                    "face_detected": False,
                    "liveness_verified": False,
                    "spoof_detected": False,
                    "blink_detected": False,
                    "blink_count": 0,
                    "left_ear": None,
                    "right_ear": None,
                    "average_ear": None,
                    "challenge": self.get_challenge_info(),
                    "reason": "Liveness challenge timed out. Issuing a new random challenge.",
                }

        try:
            results = self.liveness_detector.process_frame(frame)
        except (Exception, OSError):
            results = None

        if not results or not getattr(results, "face_landmarks", None):
            return {
                "face_detected": bool(face_bbox is not None),
                "liveness_verified": self.liveness_verified,
                "spoof_detected": False,
                "blink_detected": False,
                "blink_count": self.blink_detector.blink_count,
                "left_ear": None,
                "right_ear": None,
                "average_ear": None,
                "challenge": self.get_challenge_info(),
                "reason": "Please look straight into the camera and blink your eyes 👁️",
            }

        landmarks = results.face_landmarks[0]

        # 1. Anti-Spoof analysis (duplicate frame, static photo, bezel, moire, glare)
        spoof_res = self.anti_spoof.analyze_frame(frame, bbox=face_bbox, landmarks=landmarks)
        if spoof_res["is_spoof"]:
            self._spoof_streak += 1
            if spoof_res.get("temporal_spoof") or self._spoof_streak >= 3:
                # Reset challenge progress so a spoofed frame cannot carry over progress
                self.reset()
            return {
                "face_detected": True,
                "liveness_verified": False,
                "spoof_detected": True,
                "spoof_reason": spoof_res["reason"],
                "spoof_metrics": spoof_res["metrics"],
                "blink_detected": False,
                "blink_count": self.blink_detector.blink_count,
                "left_ear": None,
                "right_ear": None,
                "average_ear": None,
                "challenge": self.get_challenge_info(),
                "reason": spoof_res["reason"],
            }

        self._spoof_streak = 0
        self._live_frames_count += 1

        # 2. Identity continuity check (prevents completing liveness with real person then swapping a photo)
        if face_embedding is not None:
            emb = np.asarray(face_embedding, dtype=np.float32)
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
                if self._anchor_embedding is None:
                    self._anchor_embedding = emb
                else:
                    sim = float(np.dot(self._anchor_embedding, emb))
                    if sim < 0.48:
                        self.reset()
                        self._anchor_embedding = emb
                        return {
                            "face_detected": True,
                            "liveness_verified": False,
                            "spoof_detected": False,
                            "blink_detected": False,
                            "blink_count": 0,
                            "left_ear": None,
                            "right_ear": None,
                            "average_ear": None,
                            "challenge": self.get_challenge_info(),
                            "reason": "Face identity changed mid-check. Restarting challenge.",
                        }

        # 3. Extract EAR, blendshapes, and 3D pose cues
        ear_info = self.blink_detector.calculate_ear(landmarks)
        blink_res = self.blink_detector.process_landmarks(landmarks)
        bs = self._extract_blendshapes(results)
        pose = self._extract_pose(results, landmarks)

        avg_ear = ear_info["average_ear"]
        blink_blend = (bs.get("eyeBlinkLeft", 0.0) + bs.get("eyeBlinkRight", 0.0)) / 2.0
        max_blink_blend = max(bs.get("eyeBlinkLeft", 0.0), bs.get("eyeBlinkRight", 0.0))
        jaw_open = bs.get("jawOpen", 0.0)
        nose_ratio = pose["nose_ratio"]
        yaw = pose["yaw"]
        mar = pose["mar"]

        # 4. Evaluate active challenge step if not yet verified
        if not self.liveness_verified:
            action = self.current_action

            if action == "BLINK":
                eyes_open = avg_ear >= 0.21 and blink_blend < 0.30
                eyes_closed = avg_ear < 0.24 or max_blink_blend > 0.28 or blink_blend > 0.24

                if getattr(self, "blink_only", False):
                    # Fast instant blink mode: trigger immediately when closed eyes or blink detector fires
                    if eyes_closed or blink_res.get("blink_detected") or self.blink_detector.blink_count > 0:
                        self._advance_or_complete()
                    elif not self._baseline_seen:
                        if eyes_open:
                            self._baseline_seen = True
                else:
                    if not self._baseline_seen:
                        if eyes_open:
                            self._baseline_seen = True
                    elif not self._peak_seen:
                        if eyes_closed:
                            self._peak_seen = True
                    else:
                        if eyes_open:
                            self._advance_or_complete()

                    # Also detect natural blink from blink detector
                    if blink_res.get("blink_detected") or self.blink_detector.blink_count > 0:
                        self._advance_or_complete()

            elif action == "OPEN_MOUTH":
                mouth_closed = jaw_open < 0.20 and mar < 0.24
                mouth_open = jaw_open > 0.30 or mar > 0.30

                if not self._baseline_seen:
                    if mouth_closed:
                        self._baseline_seen = True
                elif not self._peak_seen:
                    if mouth_open:
                        self._peak_seen = True
                else:
                    if mouth_closed:
                        self._advance_or_complete()

            elif action == "TURN_LEFT":
                is_center = 0.38 <= nose_ratio <= 0.62 and abs(yaw) < 12.0
                turned_left = nose_ratio < 0.37 and (abs(yaw) > 8.5 or abs(nose_ratio - 0.5) > 0.14)

                if not self._baseline_seen:
                    if is_center:
                        self._baseline_seen = True
                        self._baseline_nose_ratio = nose_ratio
                elif not self._peak_seen:
                    if turned_left:
                        self._peak_seen = True
                else:
                    if is_center:
                        self._advance_or_complete()

            elif action == "TURN_RIGHT":
                is_center = 0.38 <= nose_ratio <= 0.62 and abs(yaw) < 12.0
                turned_right = nose_ratio > 0.63 and (abs(yaw) > 8.5 or abs(nose_ratio - 0.5) > 0.14)

                if not self._baseline_seen:
                    if is_center:
                        self._baseline_seen = True
                        self._baseline_nose_ratio = nose_ratio
                elif not self._peak_seen:
                    if turned_right:
                        self._peak_seen = True
                else:
                    if is_center:
                        self._advance_or_complete()

        # In blink-only mode: instant verification on blink, no multi-frame lag
        if getattr(self, "blink_only", False):
            verified_now = bool(self.liveness_verified)
            challenge_info = None
            if verified_now:
                reason = "Eye blink verified. Genuine live face."
            else:
                reason = "Please blink your eyes 👁️"
        else:
            # Multi-step challenge mode: require at least 4 distinct live frames
            verified_now = bool(self.liveness_verified and self._live_frames_count >= 4)
            challenge_info = self.get_challenge_info()

            if verified_now:
                reason = "Genuine live face verified."
            elif not self._baseline_seen:
                reason = f"Step {challenge_info['step']}/{challenge_info['total_steps']}: Look straight at the camera ({challenge_info['title']})."
            elif not self._peak_seen:
                reason = f"Step {challenge_info['step']}/{challenge_info['total_steps']}: {challenge_info['instruction']}"
            else:
                reason = f"Step {challenge_info['step']}/{challenge_info['total_steps']}: Great! Now relax / look straight to finish step."

        return {
            "face_detected": True,
            "liveness_verified": verified_now,
            "spoof_detected": False,
            "blink_detected": bool(blink_res.get("blink_detected", False) or getattr(self.blink_detector, "blink_count", 0) > 0 or self._peak_seen),
            "blink_count": blink_res.get("blink_count", getattr(self.blink_detector, "blink_count", 0)),
            "left_ear": ear_info["left_ear"],
            "right_ear": ear_info["right_ear"],
            "average_ear": avg_ear,
            "challenge": challenge_info,
            "reason": reason,
        }

    def close(self):
        if hasattr(self, "liveness_detector") and self.liveness_detector:
            self.liveness_detector.close()
