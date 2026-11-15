from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_current_user, require_admin
from backend.services.attendance_session_service import (
    start_session,
    get_session,
    get_all_sessions,
    get_sessions_by_exam,
    end_session,
)


router = APIRouter(
    prefix="/sessions",
    tags=["Attendance Sessions"],
)


@router.post("/")
def create_session(
    exam_id: int | None = None,
    current_admin: dict = Depends(require_admin),
):
    """
    Start a new attendance session (Admin only).
    """
    try:
        session_id = start_session(exam_id, created_by=current_admin["username"])

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "status": "success",
        "message": "Attendance session started successfully.",
        "session": get_session(session_id),
    }


@router.get("/")
def read_sessions(current_admin: dict = Depends(require_admin)):
    """
    Get all attendance sessions (Admin only).
    """

    sessions = get_all_sessions()

    return {
        "status": "success",
        "count": len(sessions),
        "sessions": sessions,
    }


@router.get("/exam/{exam_id}")
def read_sessions_by_exam(
    exam_id: int,
    current_admin: dict = Depends(require_admin),
):
    """
    Get all attendance sessions for an exam (Admin only).
    """

    sessions = get_sessions_by_exam(exam_id)

    return {
        "status": "success",
        "exam_id": exam_id,
        "count": len(sessions),
        "sessions": sessions,
    }


@router.get("/{session_id}")
def read_session(
    session_id: int,
    current_admin: dict = Depends(require_admin),
):
    """
    Get a single attendance session (Admin only).
    """

    session = get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found.",
        )

    return {
        "status": "success",
        "session": session,
    }


@router.put("/{session_id}/end")
def end_attendance_session(
    session_id: int,
    current_user: dict = Depends(get_current_user),
):
    """
    End an attendance session (Admin or session creator).
    """

    session = get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found.",
        )

    if (
        current_user.get("role") != "admin"
        and session.get("created_by") != current_user.get("username")
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to end this session.",
        )

    if session["ended_at"] is not None:
        raise HTTPException(
            status_code=400,
            detail="Attendance session has already ended.",
        )

    ended = end_session(session_id)

    if not ended:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found.",
        )

    return {
        "status": "success",
        "message": "Attendance session ended successfully.",
        "session": get_session(session_id),
    }