class EyeLandmarks:
    """
    Extracts the six required landmark points
    for each eye from MediaPipe Face Landmarker results.
    """

    # MediaPipe Face Mesh landmark indices.
    # These six points are used by the EAR calculation.

    LEFT_EYE_INDICES = [
        33,    # Outer corner
        160,   # Upper-left
        158,   # Upper-right
        133,   # Inner corner
        153,   # Lower-right
        144,   # Lower-left
    ]

    RIGHT_EYE_INDICES = [
        362,   # Inner corner
        385,   # Upper-left
        387,   # Upper-right
        263,   # Outer corner
        373,   # Lower-right
        380,   # Lower-left
    ]

    @staticmethod
    def _get_point(landmark):
        """
        Convert a MediaPipe landmark into a 2D point.
        """

        return [
            landmark.x,
            landmark.y,
        ]

    @classmethod
    def get_left_eye(cls, landmarks):
        """
        Extract six landmarks for the left eye.

        Returns:
            list: Six 2D points.
        """

        if landmarks is None:
            raise ValueError(
                "Face landmarks cannot be None."
            )

        return [
            cls._get_point(landmarks[index])
            for index in cls.LEFT_EYE_INDICES
        ]

    @classmethod
    def get_right_eye(cls, landmarks):
        """
        Extract six landmarks for the right eye.

        Returns:
            list: Six 2D points.
        """

        if landmarks is None:
            raise ValueError(
                "Face landmarks cannot be None."
            )

        return [
            cls._get_point(landmarks[index])
            for index in cls.RIGHT_EYE_INDICES
        ]

    @classmethod
    def get_both_eyes(cls, landmarks):
        """
        Extract six landmarks for both eyes.

        Returns:
            dict containing left and right eye points.
        """

        return {
            "left_eye": cls.get_left_eye(landmarks),
            "right_eye": cls.get_right_eye(landmarks),
        }