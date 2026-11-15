import asyncio
import time
import cv2
import numpy as np

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from backend.api.dependencies import get_current_user, require_admin
from backend.services.attendance_session_service import get_session
from backend.services.verification_session_service import VerificationSessionService
from backend.services.attendance_processing_service import AttendanceProcessingService


router = APIRouter(
    prefix="/attendance/verify",
    tags=["Attendance Verification Session"],
)


verification_session_service = VerificationSessionService()
attendance_processing_service = AttendanceProcessingService()


def _assert_session_owner(verification_session_id: str, current_user: dict):
    meta = verification_session_service.get_session_meta(verification_session_id)
    if current_user.get("role") == "admin":
        return meta
    if meta.get("owner_username") != current_user.get("username"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this verification session.",
        )
    return meta


@router.post("/start")
def start_verification_session(
    session_id: int,
    current_admin: dict = Depends(require_admin),
):
    attendance_session = get_session(session_id)

    if attendance_session is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found.",
        )

    if attendance_session["ended_at"] is not None:
        raise HTTPException(
            status_code=400,
            detail="Attendance session has already ended.",
        )

    verification_session_id = verification_session_service.create_session(
        attendance_session_id=session_id,
        owner_username=current_admin["username"],
        owner_role=current_admin["role"],
        expected_student_id=None,
    )

    challenge = verification_session_service.get_challenge_info(verification_session_id)

    return {
        "status": "success",
        "message": "Verification session started successfully.",
        "attendance_session_id": session_id,
        "verification_session_id": verification_session_id,
        "challenge": challenge,
    }


@router.post("/frame")
async def process_verification_frame(
    verification_session_id: str | None = Query(None),
    verification_session_id_form: str | None = Form(None, alias="verification_session_id"),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    t_start = time.perf_counter()
    vsid = verification_session_id or verification_session_id_form

    if not vsid or not verification_session_service.session_exists(vsid):
        raise HTTPException(
            status_code=404,
            detail="Verification session not found.",
        )

    _assert_session_owner(vsid, current_user)

    if not image.content_type:
        raise HTTPException(
            status_code=400,
            detail="Image file type could not be determined.",
        )

    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be an image.",
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    t_dec_start = time.perf_counter()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    decode_ms = (time.perf_counter() - t_dec_start) * 1000.0

    if frame is None:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file could not be decoded as an image.",
        )

    t_inf_start = time.perf_counter()
    try:
        verification = await asyncio.to_thread(
            verification_session_service.process_frame,
            vsid,
            frame,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
    inference_ms = (time.perf_counter() - t_inf_start) * 1000.0
    total_ms = (time.perf_counter() - t_start) * 1000.0
    fps = round(1000.0 / total_ms, 1) if total_ms > 0 else 0.0

    challenge = verification.get("challenge") or verification_session_service.get_challenge_info(
        vsid
    )

    return {
        "status": "success",
        "verification_session_id": vsid,
        "verification": verification,
        "challenge": challenge,
        "timing_ms": {
            "decode": round(decode_ms, 1),
            "inference": round(inference_ms, 1),
            "total": round(total_ms, 1),
            "fps": fps,
        },
    }


@router.post("/complete")
def complete_attendance_verification(
    verification_session_id: str | None = Query(None),
    verification_session_id_form: str | None = Form(None, alias="verification_session_id"),
    attendance_date: str = Form(...),
    attendance_time: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    vsid = verification_session_id or verification_session_id_form
    if not vsid or not verification_session_service.session_exists(vsid):
        raise HTTPException(
            status_code=404,
            detail="Verification session not found.",
        )

    meta = _assert_session_owner(vsid, current_user)

    if current_user.get("role") != "admin" and verification_session_service.is_completed(vsid):
        raise HTTPException(
            status_code=400,
            detail="Verification session has already been completed. Reset or start a new session.",
        )

    try:
        attendance_session_id = verification_session_service.get_attendance_session_id(
            vsid
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if attendance_session_id is None:
        raise HTTPException(
            status_code=400,
            detail="Verification session is not linked to an attendance session.",
        )

    attendance_session = get_session(attendance_session_id)
    if attendance_session is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found.",
        )

    if attendance_session["ended_at"] is not None:
        raise HTTPException(
            status_code=400,
            detail="Attendance session has already ended.",
        )

    try:
        verification = verification_session_service.get_latest_verification(
            vsid
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if verification is None:
        raise HTTPException(
            status_code=400,
            detail="No verification result is available. Process live frames first.",
        )

    # Process all verified faces in the frame (multi-face attendance support)
    marked_list = []
    candidates = (
        verification.get("results")
        if isinstance(verification.get("results"), list) and verification.get("results")
        else [verification]
    )

    for face_item in candidates:
        if (
            face_item.get("verified")
            and not face_item.get("spoof_detected")
            and face_item.get("student_id")
        ):
            # Student ownership guard
            if (
                current_user.get("role") == "user"
                and str(face_item.get("student_id")) != str(current_user.get("username"))
            ):
                continue
            try:
                att_res = attendance_processing_service.process_verification(
                    session_id=attendance_session_id,
                    verification=face_item,
                    attendance_date=attendance_date,
                    attendance_time=attendance_time,
                )
                marked_list.append({
                    **face_item,
                    "attendance_marked": att_res.get("attendance_marked", False),
                    "reason": att_res.get("reason", "Attendance processed"),
                    "record_id": att_res.get("record_id"),
                })
            except Exception as e:
                marked_list.append({
                    **face_item,
                    "attendance_marked": False,
                    "reason": str(e),
                })

    if not marked_list:
        return {
            "status": "success",
            "message": "Attendance was not marked because genuine live verification was incomplete or failed.",
            "verification_session_id": vsid,
            "attendance_session_id": attendance_session_id,
            "verification": verification,
            "attendance": {
                "attendance_marked": False,
                "reason": verification.get("reason", "Verification incomplete."),
            },
            "marked_list": [],
        }

    if current_user.get("role") != "admin":
        verification_session_service.mark_completed(vsid)

    return {
        "status": "success",
        "message": f"Attendance verification completed for {len(marked_list)} student(s).",
        "verification_session_id": vsid,
        "attendance_session_id": attendance_session_id,
        "verification": verification,
        "attendance": marked_list[0],
        "marked_list": marked_list,
    }


@router.post("/reset")
def reset_verification_session(
    verification_session_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    if not verification_session_service.session_exists(verification_session_id):
        raise HTTPException(
            status_code=404,
            detail="Verification session not found.",
        )

    _assert_session_owner(verification_session_id, current_user)

    try:
        verification_session_service.reset_session(verification_session_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    challenge = verification_session_service.get_challenge_info(verification_session_id)

    return {
        "status": "success",
        "message": "Verification session reset successfully.",
        "verification_session_id": verification_session_id,
        "challenge": challenge,
    }


@router.post("/close-session")
def close_verification_session(
    verification_session_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    if not verification_session_service.session_exists(verification_session_id):
        raise HTTPException(
            status_code=404,
            detail="Verification session not found.",
        )

    _assert_session_owner(verification_session_id, current_user)

    closed = verification_session_service.close_session(verification_session_id)
    if not closed:
        raise HTTPException(
            status_code=404,
            detail="Verification session not found.",
        )

    return {
        "status": "success",
        "message": "Verification session closed successfully.",
        "verification_session_id": verification_session_id,
    }
