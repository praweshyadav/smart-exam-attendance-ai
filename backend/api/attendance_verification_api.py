import asyncio
import base64
import time
import cv2
import numpy as np

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.api.dependencies import get_current_user
from backend.services.attendance_processing_service import AttendanceProcessingService
from backend.services.attendance_session_service import get_session
from backend.services.verification_session_service import VerificationSessionService


router = APIRouter(
    prefix="/attendance",
    tags=["Attendance Verification"],
)


# Stateful per-(user, attendance_session) verification sessions so single-frame photo
# submissions can NEVER bypass challenge-response & anti-spoofing liveness.
_session_verifiers = VerificationSessionService()
_session_key_to_vsid: dict[tuple[str, int], str] = {}

attendance_processing_service = AttendanceProcessingService()


def _get_or_create_vsid(username: str, role: str, session_id: int) -> str:
    key = (username, int(session_id))
    vsid = _session_key_to_vsid.get(key)
    if vsid and _session_verifiers.session_exists(vsid):
        return vsid
    expected_sid = username if role == "user" else None
    vsid = _session_verifiers.create_session(
        attendance_session_id=session_id,
        owner_username=username,
        owner_role=role,
        expected_student_id=expected_sid,
    )
    _session_key_to_vsid[key] = vsid
    return vsid


def _process_frame_sync(
    frame,
    session_id: int,
    attendance_date: str,
    attendance_time: str,
    student_name: str | None,
    current_user: dict,
):
    t_inf_start = time.perf_counter()
    vsid = _get_or_create_vsid(current_user["username"], current_user["role"], session_id)
    verification = _session_verifiers.process_frame(vsid, frame)
    inference_ms = (time.perf_counter() - t_inf_start) * 1000.0

    t_db_start = time.perf_counter()
    processed_results = []
    face_list = verification.get("results", [])

    for face_ver in face_list:
        sid = face_ver.get("student_id")
        sname = face_ver.get("student_name") or student_name

        # Strictly block marking unless verified + liveness_verified + not spoof
        if (
            face_ver.get("verified")
            and face_ver.get("liveness_verified")
            and not face_ver.get("spoof_detected")
            and sid
        ):
            if current_user.get("role") == "user" and str(sid) != str(current_user["username"]):
                face_ver["verified"] = False
                face_ver["attendance_marked"] = False
                face_ver["reason"] = "Students can only mark their own attendance."
            else:
                try:
                    att_res = attendance_processing_service.process_verification(
                        session_id=session_id,
                        verification=face_ver,
                        attendance_date=attendance_date,
                        attendance_time=attendance_time,
                        student_name=sname,
                    )
                    face_ver["attendance_marked"] = att_res.get("attendance_marked", False)
                    face_ver["reason"] = att_res.get("reason", face_ver.get("reason"))
                    face_ver["verification_attempt_id"] = att_res.get("verification_attempt_id")
                    # Reset challenge after completion so another student/attempt gets a fresh challenge
                    if att_res.get("attendance_marked"):
                        _session_verifiers.reset_session(vsid)
                except Exception as e:
                    face_ver["attendance_marked"] = False
                    face_ver["reason"] = f"Attendance processing failed: {str(e)}"
        else:
            face_ver["attendance_marked"] = False

        processed_results.append(face_ver)

    db_ms = (time.perf_counter() - t_db_start) * 1000.0

    verification["results"] = processed_results
    primary_attendance = (
        processed_results[0]
        if processed_results
        else {
            "success": False,
            "verified": False,
            "attendance_marked": False,
            "liveness_verified": False,
            "reason": verification.get("reason", "No face detected."),
        }
    )

    return verification, primary_attendance, processed_results, inference_ms, db_ms


@router.post("/verify")
async def verify_and_process_attendance(
    session_id: int = Form(...),
    attendance_date: str = Form(...),
    attendance_time: str = Form(...),
    student_name: str | None = Form(None),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Stateful anti-spoof attendance verification endpoint.
    Requires multi-frame liveness & active challenge completion; single photos cannot mark attendance.
    """
    t_start = time.perf_counter()

    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Attendance session not found.")

    if (
        current_user.get("role") != "admin"
        and session.get("created_by")
        and session.get("created_by") != current_user.get("username")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only verify attendance inside their own session.",
        )

    if not image.content_type:
        raise HTTPException(status_code=400, detail="Image file type could not be determined.")

    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    t_dec_start = time.perf_counter()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    decode_ms = (time.perf_counter() - t_dec_start) * 1000.0

    if frame is None:
        raise HTTPException(status_code=400, detail="Uploaded file could not be decoded as an image.")

    try:
        verification, primary_attendance, processed_results, inference_ms, db_ms = await asyncio.to_thread(
            _process_frame_sync,
            frame,
            session_id,
            attendance_date,
            attendance_time,
            student_name,
            current_user,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    total_ms = (time.perf_counter() - t_start) * 1000.0
    fps = round(1000.0 / total_ms, 1) if total_ms > 0 else 0.0

    return {
        "status": "success",
        "faces_count": len(processed_results),
        "results": processed_results,
        "verification": verification,
        "attendance": primary_attendance,
        "timing_ms": {
            "decode": round(decode_ms, 1),
            "inference": round(inference_ms, 1),
            "db": round(db_ms, 1),
            "total": round(total_ms, 1),
            "fps": fps,
        },
    }


@router.post("/verify/reset-liveness")
def reset_attendance_verification(current_user: dict = Depends(get_current_user)):
    uname = current_user["username"]
    for (u, sid), vsid in list(_session_key_to_vsid.items()):
        if u == uname or current_user.get("role") == "admin":
            if _session_verifiers.session_exists(vsid):
                _session_verifiers.reset_session(vsid)
    return {
        "status": "success",
        "message": "Attendance verification liveness reset successfully.",
    }


@router.post("/verify/close")
def close_attendance_verification(current_user: dict = Depends(get_current_user)):
    uname = current_user["username"]
    for (u, sid), vsid in list(_session_key_to_vsid.items()):
        if u == uname or current_user.get("role") == "admin":
            _session_verifiers.close_session(vsid)
            _session_key_to_vsid.pop((u, sid), None)
    return {
        "status": "success",
        "message": "Attendance verification resources closed successfully.",
    }
