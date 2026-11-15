from collections import deque
import hashlib
import cv2
import numpy as np


class AntiSpoofDetector:
    """
    Multi-cue passive anti-spoofing detector to reject printed photos,
    phone/tablet screen replays, and frozen/injected image frames.

    Combines:
    1. Exact duplicate / replayed frame hash detection
    2. Temporal face-ROI pixel & landmark micro-motion analysis (catches static photos)
    3. Screen/photo rectangular bezel line detection around the face
    4. 2D FFT Moire / LCD pixel-grid frequency spike detection
    5. Specular screen glare & sharpness checks
    """

    def __init__(self, history_size: int = 8):
        self.history_size = history_size
        self._frame_hashes = deque(maxlen=history_size)
        self._prev_roi_96 = None
        self._prev_landmarks = None
        self._static_streak = 0
        self._duplicate_streak = 0
        self._spoof_flags_window = deque(maxlen=5)
        self._hann_128 = np.outer(np.hanning(128), np.hanning(128)).astype(np.float32)
        yy, xx = np.ogrid[:128, :128]
        dist = np.sqrt((xx - 64) ** 2 + (yy - 64) ** 2)
        self._annulus_mask = (dist >= 14) & (dist <= 56)

    def reset(self):
        self._frame_hashes.clear()
        self._prev_roi_96 = None
        self._prev_landmarks = None
        self._static_streak = 0
        self._duplicate_streak = 0
        self._spoof_flags_window.clear()

    @staticmethod
    def _clamp_bbox(bbox, width: int, height: int):
        if bbox is None or len(bbox) < 4:
            # Fallback to central 60% crop if bbox is unavailable
            x1 = int(width * 0.2)
            y1 = int(height * 0.15)
            x2 = int(width * 0.8)
            y2 = int(height * 0.85)
            return x1, y1, x2, y2
        x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
        x1 = max(0, min(x1, width - 2))
        y1 = max(0, min(y1, height - 2))
        x2 = max(x1 + 2, min(x2, width))
        y2 = max(y1 + 2, min(y2, height))
        return x1, y1, x2, y2

    def _detect_bezel_frame(self, frame: np.ndarray, bbox_xyxy: tuple[int, int, int, int]) -> tuple[bool, dict]:
        """Detect rectangular phone/tablet/photo borders framing the face."""
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = bbox_xyxy
        fw, fh = x2 - x1, y2 - y1
        if fw < 40 or fh < 40:
            return False, {"horiz_lines": 0, "vert_lines": 0}

        # Expand region around face to catch enclosing device/photo edges
        pad_x = int(fw * 0.55)
        pad_y = int(fh * 0.45)
        cx1 = max(0, x1 - pad_x)
        cy1 = max(0, y1 - pad_y)
        cx2 = min(w, x2 + pad_x)
        cy2 = min(h, y2 + pad_y)

        context = frame[cy1:cy2, cx1:cx2]
        if context.size == 0:
            return False, {"horiz_lines": 0, "vert_lines": 0}

        gray = cv2.cvtColor(context, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 160)

        # Mask out the inner face region (inset slightly inside bbox) so facial contours don't count as bezels
        ix1 = max(0, (x1 - cx1) + int(fw * 0.08))
        iy1 = max(0, (y1 - cy1) + int(fh * 0.08))
        ix2 = min(context.shape[1], (x2 - cx1) - int(fw * 0.08))
        iy2 = min(context.shape[0], (y2 - cy1) - int(fh * 0.08))
        if ix2 > ix1 and iy2 > iy1:
            edges[iy1:iy2, ix1:ix2] = 0

        min_len = max(35, int(min(fw, fh) * 0.45))
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=45,
            minLineLength=min_len,
            maxLineGap=10,
        )

        horiz = 0
        vert = 0
        if lines is not None:
            for lx1, ly1, lx2, ly2 in np.asarray(lines).reshape(-1, 4):
                dx = abs(int(lx2) - int(lx1))
                dy = abs(int(ly2) - int(ly1))
                length = np.hypot(dx, dy)
                if length < min_len:
                    continue
                if dy <= dx * 0.14:
                    horiz += 1
                elif dx <= dy * 0.14:
                    vert += 1

        bezel_detected = horiz >= 2 and vert >= 2
        return bezel_detected, {"horiz_lines": horiz, "vert_lines": vert}

    def analyze_static_cues(self, frame: np.ndarray, bbox=None) -> dict:
        """
        Evaluate spatial anti-spoof signals on a single frame (FFT moire, bezel, glare, blur).
        Safe to run standalone or as part of temporal multi-frame session analysis.
        """
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = self._clamp_bbox(bbox, w, h)
        face_roi = frame[y1:y2, x1:x2]

        gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        roi_128 = cv2.resize(gray_face, (128, 128)).astype(np.float32)
        roi_fft = cv2.resize(gray_face, (128, 128), interpolation=cv2.INTER_NEAREST).astype(np.float32)

        # 1. Sharpness / Laplacian variance
        lap_var = float(cv2.Laplacian(roi_128, cv2.CV_32F).var())
        blur_spoof = lap_var < 10.0

        # 2. 2D FFT Moire / periodic screen pixel-grid check
        centered = roi_fft - float(roi_fft.mean())
        mag = np.abs(np.fft.fftshift(np.fft.fft2(centered * self._hann_128)))
        annulus = mag[self._annulus_mask]
        moire_peak_ratio = float(annulus.max() / (np.median(annulus) + 1e-6)) if annulus.size else 0.0
        strong_moire = moire_peak_ratio > 88.0
        soft_moire = moire_peak_ratio > 58.0

        # 3. Specular screen / glossy photo glare check
        hsv = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
        glare_mask = (hsv[:, :, 2] >= 248) & (hsv[:, :, 1] <= 20)
        glare_ratio = float(np.mean(glare_mask))
        strong_glare = glare_ratio > 0.16
        soft_glare = glare_ratio > 0.08

        # 4. Rectangular screen/photo bezel framing the face
        bezel_detected, bezel_meta = self._detect_bezel_frame(frame, (x1, y1, x2, y2))
        strong_bezel = bezel_meta["horiz_lines"] >= 6 and bezel_meta["vert_lines"] >= 6

        reasons = []
        risk = 0.0

        if blur_spoof:
            risk += 0.55
            reasons.append("Image too blurry or low-detail for genuine verification.")
        if strong_moire:
            risk += 0.85
            reasons.append("Screen pixel/moire pattern detected.")
        elif soft_moire:
            risk += 0.35

        if strong_glare:
            risk += 0.55
            reasons.append("Strong screen/photo glare detected.")
        elif soft_glare:
            risk += 0.25

        if strong_bezel:
            risk += 0.85
            reasons.append("Phone/tablet screen or photo border detected around face.")
        elif bezel_detected:
            risk += 0.50
            if soft_glare or soft_moire:
                risk += 0.35
                reasons.append("Phone/tablet screen or photo frame detected around face.")

        is_spoof = (
            strong_moire
            or blur_spoof
            or strong_bezel
            or (bezel_detected and (soft_glare or soft_moire or strong_glare))
            or risk >= 0.85
        )

        return {
            "is_spoof": bool(is_spoof),
            "risk_score": round(min(1.0, risk), 3),
            "reasons": reasons,
            "metrics": {
                "laplacian_var": round(lap_var, 2),
                "moire_peak_ratio": round(moire_peak_ratio, 2),
                "glare_ratio": round(glare_ratio, 4),
                "bezel_detected": bezel_detected,
                **bezel_meta,
            },
        }

    def analyze_frame(self, frame: np.ndarray, bbox=None, landmarks=None) -> dict:
        """
        Evaluate both spatial AND temporal anti-spoof signals across consecutive frames.
        Rejects static photos, identical/replayed frames, and screen replays.
        """
        if frame is None:
            raise ValueError("Frame cannot be None.")

        h, w = frame.shape[:2]
        x1, y1, x2, y2 = self._clamp_bbox(bbox, w, h)
        face_roi = frame[y1:y2, x1:x2]
        gray_96 = cv2.resize(cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY), (96, 96))

        # 1. Exact duplicate frame check (rejects resubmitted single photo bytes/arrays)
        frame_small = cv2.resize(frame, (128, 96))
        frame_hash = hashlib.sha256(frame_small.tobytes()).hexdigest()
        if self._frame_hashes and frame_hash == self._frame_hashes[-1]:
            self._duplicate_streak += 1
        elif frame_hash in self._frame_hashes:
            self._duplicate_streak += 1
        else:
            self._duplicate_streak = 0
        self._frame_hashes.append(frame_hash)

        # 2. Temporal pixel motion & landmark micro-motion check (catches frozen photo)
        roi_mae = None
        if self._prev_roi_96 is not None:
            roi_mae = float(np.mean(np.abs(gray_96.astype(np.float32) - self._prev_roi_96.astype(np.float32))))
        self._prev_roi_96 = gray_96

        landmark_delta = None
        if landmarks is not None and len(landmarks) >= 468:
            key_idx = [1, 33, 61, 133, 199, 263, 291, 362]
            cur_pts = np.array([[landmarks[i].x, landmarks[i].y] for i in key_idx], dtype=np.float32)
            if self._prev_landmarks is not None:
                landmark_delta = float(np.mean(np.linalg.norm(cur_pts - self._prev_landmarks, axis=1)))
            self._prev_landmarks = cur_pts

        if roi_mae is not None and roi_mae < 0.85 and (landmark_delta is None or landmark_delta < 0.0008):
            self._static_streak += 1
        elif roi_mae is not None and roi_mae >= 1.1:
            self._static_streak = 0

        # 3. Spatial anti-spoof checks
        static_res = self.analyze_static_cues(frame, bbox=(x1, y1, x2, y2))

        reasons = list(static_res["reasons"])
        temporal_spoof = False

        if self._duplicate_streak >= 1:
            temporal_spoof = True
            reasons.insert(0, "Frozen or duplicate image frame detected. Use a live camera feed.")
        elif self._static_streak >= 3:
            temporal_spoof = True
            reasons.insert(0, "Static photo detected. Move naturally in front of the camera.")

        frame_flag = bool(static_res["is_spoof"] or temporal_spoof)
        self._spoof_flags_window.append(1 if static_res["is_spoof"] else 0)
        sustained_spatial_spoof = sum(self._spoof_flags_window) >= 3

        is_spoof = bool(temporal_spoof or static_res["is_spoof"] or sustained_spatial_spoof)
        if is_spoof and not reasons:
            reasons.append("Possible photo or screen replay detected. Show your live face directly.")

        return {
            "is_spoof": is_spoof,
            "temporal_spoof": temporal_spoof,
            "static_streak": self._static_streak,
            "duplicate_streak": self._duplicate_streak,
            "roi_mae": round(roi_mae, 3) if roi_mae is not None else None,
            "landmark_delta": round(landmark_delta, 5) if landmark_delta is not None else None,
            "risk_score": 1.0 if temporal_spoof else static_res["risk_score"],
            "reason": reasons[0] if reasons else "Live frame cues normal.",
            "reasons": reasons,
            "metrics": static_res["metrics"],
        }
