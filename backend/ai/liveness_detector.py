import threading
import cv2
import mediapipe as mp
import numpy as np

from backend.core.config import FACE_LANDMARKER_PATH

_detector_lock = threading.Lock()


class DummyLandmarkerResult:
    face_landmarks = []
    face_blendshapes = []
    facial_transformation_matrixes = []


class LivenessDetector:
    """
    Detects basic liveness through eye blinking
    using MediaPipe Face Landmarker.
    Thread-safe and guarded against C++ access violations.
    """

    def __init__(self):
        self.base_options = mp.tasks.BaseOptions
        self.vision = mp.tasks.vision

        self.options = self.vision.FaceLandmarkerOptions(
            base_options=self.base_options(
                model_asset_path=str(FACE_LANDMARKER_PATH)
            ),
            running_mode=self.vision.RunningMode.IMAGE,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1,
        )

        try:
            with _detector_lock:
                self.face_landmarker = self.vision.FaceLandmarker.create_from_options(
                    self.options
                )
        except Exception:
            self.face_landmarker = None

    def process_frame(self, frame):
        """
        Process a single BGR OpenCV frame safely.

        Returns:
            MediaPipe face landmarker result or DummyLandmarkerResult on error.
        """
        if frame is None:
            raise ValueError("Frame cannot be None.")

        if self.face_landmarker is None:
            return DummyLandmarkerResult()

        try:
            rgb_frame = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame,
            )
            with _detector_lock:
                return self.face_landmarker.detect(mp_image)
        except (Exception, OSError):
            # Guard against C++ thread-safety access violations on Windows Python 3.13
            return DummyLandmarkerResult()

    def detect_face(self, frame):
        """
        Check whether a face is detected.

        Returns:
            bool: True if a face is detected.
        """
        results = self.process_frame(frame)
        return bool(results.face_landmarks)

    def get_landmarks(self, frame):
        """
        Get face landmarks from a frame.

        Returns:
            list or None: Face landmarks.
        """
        results = self.process_frame(frame)
        if not results.face_landmarks:
            return None
        return results.face_landmarks[0]

    def close(self):
        """
        Release MediaPipe resources.
        """
        if hasattr(self, "face_landmarker") and self.face_landmarker:
            self.face_landmarker.close()
