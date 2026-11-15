import cv2
import numpy as np

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.api.dependencies import get_current_user
from backend.core.config import LIVENESS_ENABLED
from backend.services.verification_service import VerificationService


router = APIRouter(
    prefix="/verification",
    tags=["Face Verification"],
)


_user_verification_services: dict[str, VerificationService] = {}


def _get_verifier(username: str) -> VerificationService:
    svc = _user_verification_services.get(username)
    if svc is None:
        svc = VerificationService(require_liveness=LIVENESS_ENABLED)
        _user_verification_services[username] = svc
    return svc


@router.post("/")
async def verify_face(
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Verify a student using a live frame sequence (anti-spoof + liveness required)."""
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

    expected_sid = current_user["username"] if current_user.get("role") == "user" else None
    verifier = _get_verifier(current_user["username"])

    try:
        result = verifier.verify_frame(frame, expected_student_id=expected_sid)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return {
        "status": "success",
        "verification": result,
    }


@router.post("/reset-liveness")
def reset_liveness(current_user: dict = Depends(get_current_user)):
    verifier = _user_verification_services.get(current_user["username"])
    if verifier:
        verifier.reset_liveness()
    return {
        "status": "success",
        "message": "Liveness state reset successfully.",
    }
