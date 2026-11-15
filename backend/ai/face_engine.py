import threading
from insightface.app import FaceAnalysis

_shared_face_engine = None
_face_engine_lock = threading.Lock()


class FaceEngine:
    """
    Handles face detection and face embedding generation
    using InsightFace.

    Optimized to load only detection and recognition models
    (ignoring 3D landmarks and gender/age predictors)
    and reuse a shared singleton instance.
    """

    def __new__(cls, *args, **kwargs):
        global _shared_face_engine
        if _shared_face_engine is None:
            with _face_engine_lock:
                if _shared_face_engine is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    _shared_face_engine = instance
        return _shared_face_engine

    def __init__(self, det_size=(640, 640)):
        if getattr(self, "_initialized", False):
            return

        with _face_engine_lock:
            if getattr(self, "_initialized", False):
                return
            # Load only required modules to maximize FPS and cut inference overhead by ~40%
            self.app = FaceAnalysis(
                name="buffalo_l",
                allowed_modules=["detection", "recognition"],
            )
            self.app.prepare(ctx_id=0, det_size=det_size)
            self._initialized = True

    def detect_faces(self, image):
        """
        Detect all faces in an image.

        Returns:
            list: Detected face objects.
        """
        return self.app.get(image)

    def get_embedding(self, face):
        """
        Extract the embedding from a detected face.

        Returns:
            numpy.ndarray: Face embedding.
        """
        return face.embedding