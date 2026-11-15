import numpy as np


class EyeAspectRatio:
    """
    Calculates the Eye Aspect Ratio (EAR)
    from eye landmark coordinates.
    """

    @staticmethod
    def calculate(eye_landmarks):
        """
        Calculate EAR for one eye.

        Expected landmark order:

            p1 -------- p4
             |          |
            p2          p3
             |          |
            p6 -------- p5

        Args:
            eye_landmarks: Six 2D points representing one eye.

        Returns:
            float: Eye Aspect Ratio.
        """

        if eye_landmarks is None:
            raise ValueError(
                "Eye landmarks cannot be None."
            )

        if len(eye_landmarks) != 6:
            raise ValueError(
                "Exactly 6 eye landmarks are required."
            )

        points = np.asarray(
            eye_landmarks,
            dtype=np.float32
        )

        if points.shape != (6, 2):
            raise ValueError(
                "Eye landmarks must have shape (6, 2)."
            )

        vertical_distance_1 = np.linalg.norm(
            points[1] - points[5]
        )

        vertical_distance_2 = np.linalg.norm(
            points[2] - points[4]
        )

        horizontal_distance = np.linalg.norm(
            points[0] - points[3]
        )

        if horizontal_distance == 0:
            raise ValueError(
                "Horizontal eye distance cannot be zero."
            )

        ear = (
            vertical_distance_1 +
            vertical_distance_2
        ) / (2.0 * horizontal_distance)

        return float(ear)