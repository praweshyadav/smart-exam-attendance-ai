from backend.ai.blink_detector import BlinkDetector
from backend.ai.liveness_detector import LivenessDetector


class LivenessService:
    """
    Handles the complete liveness verification process.

    The service combines MediaPipe face landmarks
    with blink detection.
    """

    def __init__(
        self,
        liveness_detector=None,
        blink_detector=None,
    ):
        self.liveness_detector = (
            liveness_detector or LivenessDetector()
        )

        self.blink_detector = (
            blink_detector or BlinkDetector()
        )

    def process_frame(self, frame):
        """
        Process one webcam frame.

        Returns:
            dict containing face detection,
            EAR values, and liveness status.
        """

        if frame is None:
            raise ValueError(
                "Frame cannot be None."
            )

        results = self.liveness_detector.process_frame(
            frame
        )

        if not results.face_landmarks:

            return {
                "face_detected": False,
                "liveness_verified": False,
                "blink_detected": False,
                "blink_count": self.blink_detector.blink_count,
                "left_ear": None,
                "right_ear": None,
                "average_ear": None,
            }

        landmarks = results.face_landmarks[0]

        blink_result = (
            self.blink_detector.process_landmarks(
                landmarks
            )
        )

        return {
            "face_detected": True,
            "liveness_verified": (
                blink_result["blink_count"] > 0
            ),
            "blink_detected": blink_result[
                "blink_detected"
            ],
            "blink_count": blink_result[
                "blink_count"
            ],
            "left_ear": blink_result[
                "left_ear"
            ],
            "right_ear": blink_result[
                "right_ear"
            ],
            "average_ear": blink_result[
                "average_ear"
            ],
        }

    def reset(self):
        """
        Reset the liveness verification state.
        """

        self.blink_detector.reset()

    def close(self):
        """
        Release MediaPipe resources.
        """

        self.liveness_detector.close()