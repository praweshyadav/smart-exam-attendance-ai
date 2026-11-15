import numpy as np

from backend.ai.face_database import FaceDatabase
from backend.ai.face_engine import FaceEngine
from backend.ai.face_validator import FaceValidator
from backend.ai.face_matcher import FaceMatcher
from backend.services.student_service import (
    student_exists,
    set_face_registered,
)


class FaceRegistrationService:
    """
    Handles complete face registration for a student.
    """

    def __init__(
        self,
        face_engine=None,
        face_database=None,
        face_matcher=None,
    ):
        self.face_engine = face_engine or FaceEngine()
        self.face_database = face_database or FaceDatabase()
        self.face_matcher = face_matcher or FaceMatcher(database=self.face_database)

    def register_face(self, student_id, image, allow_update=False, pre_detected_faces=None):
        """
        Register a student's face from an image.

        Returns:
            dict containing registration result and reason.
        """
        if not student_id:
            return {
                "success": False,
                "reason": "Student ID cannot be empty."
            }

        # 1. Verify student exists in the database.
        if not student_exists(student_id):
            return {
                "success": False,
                "reason": "Student does not exist."
            }

        # 2. Check if already registered and updates not allowed
        if not allow_update and self.face_database.embedding_exists(student_id):
            return {
                "success": False,
                "reason": "Face is already registered."
            }

        # 3. Detect faces (reuses pre-detected faces to eliminate redundant inference)
        faces = pre_detected_faces if pre_detected_faces is not None else self.face_engine.detect_faces(image)

        # Filter valid faces (ignore tiny background faces or low-confidence noise)
        valid_faces = []
        if faces:
            for f in faces:
                score = getattr(f, "det_score", 1.0)
                if score is not None and score < 0.60:
                    continue
                if hasattr(f, "bbox") and f.bbox is not None:
                    x1, y1, x2, y2 = f.bbox
                    if (x2 - x1) < 70 or (y2 - y1) < 70:
                        continue
                valid_faces.append(f)

        if not valid_faces:
            return {
                "success": False,
                "reason": "No clear face detected. Please face the camera with good lighting.",
            }

        valid_faces.sort(
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
            if hasattr(f, "bbox") and f.bbox is not None
            else 0,
            reverse=True,
        )

        if len(valid_faces) > 1:
            p_area = (valid_faces[0].bbox[2] - valid_faces[0].bbox[0]) * (valid_faces[0].bbox[3] - valid_faces[0].bbox[1])
            s_area = (valid_faces[1].bbox[2] - valid_faces[1].bbox[0]) * (valid_faces[1].bbox[3] - valid_faces[1].bbox[1])
            if p_area > 0 and (s_area / p_area) > 0.40:
                return {
                    "success": False,
                    "reason": "Multiple faces detected. Please ensure only one student is in frame.",
                }

        # 4. Validate primary face embedding
        primary_face = valid_faces[0]
        validation = FaceValidator.validate([primary_face])

        if not validation["valid"]:
            return {
                "success": False,
                "reason": validation["reason"]
            }

        # 5. Extract the embedding and normalize to unit vector
        embedding = np.asarray(self.face_engine.get_embedding(primary_face), dtype=np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        # 5b. Prevent registering face already associated with another student
        match = self.face_matcher.find_best_match(embedding)
        if match["matched"] and str(match["student_id"]) != str(student_id):
            return {
                "success": False,
                "reason": f"Face is already registered under Roll/ID: {match['student_id']}."
            }

        # 6. Save or update the embedding (normalized to unit vector)
        if self.face_database.embedding_exists(student_id):
            self.face_database.update_embedding(student_id, embedding)
        else:
            saved = self.face_database.save_embedding(
                student_id,
                embedding
            )
            if not saved:
                return {
                    "success": False,
                    "reason": "Face embedding could not be saved."
                }

        # 7. Generate base64 face image for database storage
        face_b64 = None
        try:
            import cv2
            import base64
            face_obj = primary_face
            if hasattr(face_obj, "bbox") and face_obj.bbox is not None:
                x1, y1, x2, y2 = face_obj.bbox.astype(int)
                h, w = image.shape[:2]
                margin = int(0.25 * max(x2 - x1, y2 - y1))
                cx1, cy1 = max(0, x1 - margin), max(0, y1 - margin)
                cx2, cy2 = min(w, x2 + margin), min(h, y2 + margin)
                crop_img = image[cy1:cy2, cx1:cx2]
                ok, buf = cv2.imencode(".jpg", crop_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                if ok:
                    face_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")
            if not face_b64:
                ok, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                if ok:
                    face_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")
        except Exception:
            face_b64 = None

        # 8. Update student's registration status in MySQL.
        updated = set_face_registered(
            student_id,
            registered=True,
            face_image=face_b64,
        )

        if not updated:
            # Roll back embedding if student status
            # could not be updated.
            self.face_database.delete_embedding(student_id)

            return {
                "success": False,
                "reason": "Student face registration status could not be updated."
            }

        return {
            "success": True,
            "reason": "Face registered successfully.",
            "student_id": student_id,
            "embedding_shape": embedding.shape,
        }
