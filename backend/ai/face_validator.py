class FaceValidator:
    """
    Validates the result of face detection before
    continuing with registration or verification.
    """

    @staticmethod
    def validate_face_count(faces):
        """
        Validate that exactly one face is detected.

        Returns:
            bool: True if exactly one face exists.
        """

        if faces is None:
            return False

        return len(faces) == 1

    @staticmethod
    def validate_embedding(face):
        """
        Validate that a detected face contains a
        valid 512-dimensional embedding.

        Returns:
            bool: True if embedding is valid.
        """

        if face is None:
            return False

        embedding = getattr(face, "embedding", None)

        if embedding is None:
            return False

        if embedding.shape != (512,):
            return False

        return True

    @classmethod
    def validate(cls, faces):
        """
        Validate both face count and embedding.

        Returns:
            dict containing validation result and reason.
        """

        if faces is None or len(faces) == 0:
            return {
                "valid": False,
                "reason": "No face detected."
            }

        if len(faces) > 1:
            return {
                "valid": False,
                "reason": "Multiple faces detected."
            }

        face = faces[0]

        if not cls.validate_embedding(face):
            return {
                "valid": False,
                "reason": "Invalid face embedding."
            }

        return {
            "valid": True,
            "reason": "Exactly one valid face detected."
        }