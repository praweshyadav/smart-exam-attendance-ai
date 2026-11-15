from backend.ai.eye_aspect_ratio import EyeAspectRatio
from backend.ai.eye_landmarks import EyeLandmarks
from backend.core.config import (
    BLINK_THRESHOLD,
    MIN_CLOSED_FRAMES,
)


class BlinkDetector:
    """
    Detects eye blinks using Eye Aspect Ratio (EAR).

    A blink is detected when the EAR falls below
    the configured threshold for a sufficient number
    of consecutive frames.
    """

    def __init__(
        self,
        blink_threshold=BLINK_THRESHOLD,
        min_closed_frames=MIN_CLOSED_FRAMES,
    ):
        if blink_threshold <= 0:
            raise ValueError(
                "Blink threshold must be greater than zero."
            )

        if min_closed_frames < 1:
            raise ValueError(
                "Minimum closed frames must be at least 1."
            )

        self.blink_threshold = blink_threshold
        self.min_closed_frames = min_closed_frames

        self.closed_frames = 0
        self.blink_count = 0

    def calculate_ear(self, landmarks):
        """
        Calculate the average EAR from face landmarks.

        Returns:
            dict containing left EAR, right EAR,
            and average EAR.
        """
        if landmarks is None:
            raise ValueError(
                "Face landmarks cannot be None."
            )

        eyes = EyeLandmarks.get_both_eyes(
            landmarks
        )

        left_ear = EyeAspectRatio.calculate(
            eyes["left_eye"]
        )

        right_ear = EyeAspectRatio.calculate(
            eyes["right_eye"]
        )

        average_ear = (
            left_ear + right_ear
        ) / 2.0

        return {
            "left_ear": left_ear,
            "right_ear": right_ear,
            "average_ear": average_ear,
        }

    def process_landmarks(self, landmarks):
        """
        Process one frame of face landmarks.

        Returns:
            dict containing EAR and blink status.
        """
        ear_data = self.calculate_ear(
            landmarks
        )

        average_ear = ear_data["average_ear"]
        blink_detected = False

        if average_ear < self.blink_threshold:
            self.closed_frames += 1
        else:
            if self.closed_frames >= self.min_closed_frames:
                self.blink_count += 1
                blink_detected = True
            self.closed_frames = 0

        return {
            "left_ear": ear_data["left_ear"],
            "right_ear": ear_data["right_ear"],
            "average_ear": average_ear,
            "blink_detected": blink_detected,
            "blink_count": self.blink_count,
        }

    def reset(self):
        """
        Reset the blink detector state.
        """
        self.closed_frames = 0
        self.blink_count = 0
