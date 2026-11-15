import asyncio
from uuid import uuid4
import cv2
import numpy as np

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from backend.ai.anti_spoof import AntiSpoofDetector
from backend.api.dependencies import ensure_self_or_admin, get_current_user, require_admin
from backend.services.challenge_liveness_service import ChallengeLivenessService
from backend.services.face_registration_service import FaceRegistrationService


router = APIRouter(
    prefix="/face-registration",
    tags=["Face Registration"],
)


face_registration_service = FaceRegistrationService()
_static_anti_spoof = AntiSpoofDetector()
_reg_liveness_sessions: dict[str, dict] = {}


@router.post("/liveness/start")
def start_registration_liveness(current_user: dict = Depends(get_current_user)):
    """Start a live-face verification session before face registration capture."""
    reg_sid = str(uuid4())
    svc = ChallengeLivenessService()
    _reg_liveness_sessions[reg_sid] = {
        "owner": current_user["username"],
        "service": svc,
        "verified": False,
    }
    return {
        "status": "success",
        "registration_session_id": reg_sid,
        "challenge": svc.get_challenge_info(),
    }


@router.post("/liveness/frame")
async def check_registration_liveness_frame(
    registration_session_id: str = Query(...),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Process a webcam frame for live registration liveness check."""
    sess = _reg_liveness_sessions.get(registration_session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Registration liveness session not found.")
    if current_user.get("role") != "admin" and sess["owner"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized for this registration session.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded frame is empty.")

    frame = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode image frame.")

    def _run():
        faces = face_registration_service.face_engine.detect_faces(frame)
        bbox = None
        emb = None
        if faces and len(faces) == 1 and hasattr(faces[0], "bbox") and faces[0].bbox is not None:
            bbox = faces[0].bbox.astype(int).tolist()
            emb = face_registration_service.face_engine.get_embedding(faces[0])
        elif faces and len(faces) > 1:
            return {
                "face_detected": True,
                "liveness_verified": False,
                "spoof_detected": False,
                "challenge": sess["service"].get_challenge_info(),
                "reason": "Multiple faces detected. Ensure only one person is in frame.",
            }
        res = sess["service"].process_frame(frame, face_bbox=bbox, face_embedding=emb)
        if res.get("liveness_verified") and not res.get("spoof_detected"):
            sess["verified"] = True
        return res

    res = await asyncio.to_thread(_run)
    return {
        "status": "success",
        "registration_session_id": registration_session_id,
        **res,
    }


@router.post("/liveness/close")
def close_registration_liveness(
    registration_session_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    sess = _reg_liveness_sessions.pop(registration_session_id, None)
    if sess and sess.get("service"):
        try:
            sess["service"].close()
        except Exception:
            pass
    return {"status": "success"}


@router.post("/")
async def register_face(
    student_id: str = Form(None),
    student_id_query: str | None = Query(None, alias="student_id"),
    allow_update: bool = Form(False),
    allow_update_query: bool = Query(False, alias="allow_update"),
    registration_session_id: str | None = Form(None),
    image: UploadFile = File(...),
    current_admin: dict = Depends(require_admin),
):
    """
    Register a student's face using an uploaded image (Admin only).
    """
    sid = student_id or student_id_query

    if not sid or not sid.strip():
        raise HTTPException(status_code=400, detail="Student ID cannot be empty.")

    sid = sid.strip()
    should_update = allow_update or allow_update_query

    if registration_session_id:
        sess = _reg_liveness_sessions.get(registration_session_id)
        if not sess or (current_admin.get("role") != "admin" and sess["owner"] != current_admin["username"]):
            raise HTTPException(status_code=400, detail="Invalid registration liveness session.")
        if not sess.get("verified"):
            raise HTTPException(
                status_code=400,
                detail="Live face liveness check is not completed yet. Complete the challenge first.",
            )

    if not image.content_type:
        raise HTTPException(status_code=400, detail="Image file type could not be determined.")

    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(status_code=400, detail="Uploaded file could not be decoded as an image.")

    # Passive anti-spoofing check on registration image (blocks screen moire / glare / bezel photos)
    faces = await asyncio.to_thread(face_registration_service.face_engine.detect_faces, frame)
    if faces and len(faces) >= 1 and hasattr(faces[0], "bbox") and faces[0].bbox is not None:
        spoof_check = _static_anti_spoof.analyze_static_cues(frame, bbox=faces[0].bbox.astype(int).tolist())
        if spoof_check.get("is_spoof"):
            raise HTTPException(
                status_code=400,
                detail=spoof_check["reasons"][0]
                if spoof_check.get("reasons")
                else "Photo/screen spoof cues detected. Use a genuine live face.",
            )

    result = await asyncio.to_thread(
        face_registration_service.register_face,
        student_id=sid,
        image=frame,
        allow_update=should_update,
        pre_detected_faces=faces,
    )

    if not result["success"]:
        reason = result["reason"]

        if reason == "Student does not exist.":
            raise HTTPException(status_code=404, detail=reason)

        if reason == "Face is already registered.":
            raise HTTPException(status_code=409, detail=reason)

        raise HTTPException(status_code=400, detail=reason)

    # Clean up registration liveness session once used
    if registration_session_id:
        sess = _reg_liveness_sessions.pop(registration_session_id, None)
        if sess and sess.get("service"):
            try:
                sess["service"].close()
            except Exception:
                pass

    embedding_shape = result.get("embedding_shape")
    if hasattr(embedding_shape, "tolist"):
        embedding_shape = embedding_shape.tolist()

    return {
        "status": "success",
        "message": result["reason"],
        "student_id": result["student_id"],
        "embedding_shape": embedding_shape,
    }


@router.post("/analyze-frame")
async def analyze_registration_frame(
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze camera feed in real-time to guide student alignment
    and auto-capture when face position and quality are optimal.
    """
    if not image.content_type or not image.content_type.startswith("image/"):
        return {"face_detected": False, "quality_ok": False, "guidance": "Invalid image"}

    image_bytes = await image.read()
    if not image_bytes:
        return {"face_detected": False, "quality_ok": False, "guidance": "Empty frame"}

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if frame is None:
        return {"face_detected": False, "quality_ok": False, "guidance": "Could not decode frame"}

    faces = await asyncio.to_thread(face_registration_service.face_engine.detect_faces, frame)

    if not faces or len(faces) == 0:
        return {
            "face_detected": False,
            "quality_ok": False,
            "bbox": None,
            "guidance": "No face detected. Please look into the camera.",
        }

    if len(faces) > 1:
        return {
            "face_detected": True,
            "quality_ok": False,
            "bbox": None,
            "guidance": "Multiple faces detected. Please ensure only one person is in the frame.",
        }

    face = faces[0]
    bbox = face.bbox.astype(int).tolist() if hasattr(face, "bbox") else None

    if not bbox or len(bbox) < 4:
        return {
            "face_detected": True,
            "quality_ok": False,
            "bbox": None,
            "guidance": "Please face the camera directly.",
        }

    x1, y1, x2, y2 = bbox
    fw = x2 - x1
    fh = y2 - y1
    h, w = frame.shape[:2]
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0

    if fw < w * 0.18 or fh < h * 0.18:
        return {
            "face_detected": True,
            "quality_ok": False,
            "bbox": bbox,
            "guidance": "Move closer to the camera.",
        }

    if fw > w * 0.85:
        return {
            "face_detected": True,
            "quality_ok": False,
            "bbox": bbox,
            "guidance": "Move back slightly from the camera.",
        }

    if abs(cx - w / 2.0) > w * 0.28 or abs(cy - h / 2.0) > h * 0.28:
        return {
            "face_detected": True,
            "quality_ok": False,
            "bbox": bbox,
            "guidance": "Center your face inside the guide.",
        }

    return {
        "face_detected": True,
        "quality_ok": True,
        "bbox": bbox,
        "guidance": "Face aligned! Hold still...",
    }
