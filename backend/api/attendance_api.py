from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import (
    ensure_self_or_admin,
    get_current_user,
    require_admin,
)

from backend.database.database import get_connection

from backend.services.attendance_service import (
    mark_attendance,
    get_attendance,
    get_attendance_by_session,
    get_attendance_by_student,
    get_attendance_by_date,
    update_attendance,
)

from backend.services.attendance_session_service import get_session
from backend.services.student_service import get_student
from backend.services.holiday_service import check_attendance_allowed


router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)


class AttendanceCreate(BaseModel):
    session_id: int
    student_id: str
    student_name: str
    attendance_date: str
    attendance_time: str
    status: str = "Present"
    verification_score: float | None = None


class AttendanceUpdate(BaseModel):
    status: str | None = None
    verification_score: float | None = None


@router.post("/")
def create_attendance(
    attendance: AttendanceCreate,
    current_admin: dict = Depends(require_admin),
):
    is_allowed, block_msg, _ = check_attendance_allowed(attendance.attendance_date)
    if not is_allowed:
        raise HTTPException(
            status_code=400,
            detail=block_msg,
        )

    session = get_session(attendance.session_id)

    if session is None:
        raise HTTPException(
            status_code=400,
            detail="Attendance session does not exist.",
        )

    student = get_student(attendance.student_id)

    if student is None:
        raise HTTPException(
            status_code=400,
            detail="Student does not exist.",
        )

    try:
        created = mark_attendance(
            session_id=attendance.session_id,
            student_id=attendance.student_id,
            student_name=attendance.student_name,
            attendance_date=attendance.attendance_date,
            attendance_time=attendance.attendance_time,
            status=attendance.status,
            verification_score=attendance.verification_score,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if not created:
        raise HTTPException(
            status_code=409,
            detail="Attendance already marked for this student in this session.",
        )

    records = get_attendance_by_session(attendance.session_id)

    created_record = next(
        (
            item
            for item in records
            if item["student_id"] == attendance.student_id
        ),
        None,
    )

    return {
        "status": "success",
        "message": "Attendance marked successfully.",
        "attendance": created_record,
    }


@router.get("/")
def read_all_attendance(current_admin: dict = Depends(require_admin)):
    with get_connection() as connection:
        records = connection.execute(
            """
            SELECT
                id,
                session_id,
                student_id,
                student_name,
                attendance_date,
                attendance_time,
                status,
                verification_score,
                face_image
            FROM attendance
            ORDER BY attendance_date DESC, attendance_time DESC
            """
        ).fetchall()

    attendance = [dict(record) for record in records]

    return {
        "status": "success",
        "count": len(attendance),
        "attendance": attendance,
    }


@router.get("/my")
def read_my_attendance(current_user: dict = Depends(get_current_user)):
    """Get attendance records for the currently logged-in student/user."""
    attendance = get_attendance_by_student(current_user["username"])
    return {
        "status": "success",
        "student_id": current_user["username"],
        "count": len(attendance),
        "attendance": attendance,
    }


@router.get("/session/{session_id}")
def read_attendance_by_session(
    session_id: int,
    current_admin: dict = Depends(require_admin),
):
    session = get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance session not found.",
        )

    attendance = get_attendance_by_session(session_id)

    return {
        "status": "success",
        "session_id": session_id,
        "count": len(attendance),
        "attendance": attendance,
    }


@router.get("/student/{student_id}")
def read_attendance_by_student(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    ensure_self_or_admin(current_user, student_id)

    student = get_student(student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    attendance = get_attendance_by_student(student_id)

    return {
        "status": "success",
        "student_id": student_id,
        "count": len(attendance),
        "attendance": attendance,
    }


@router.get("/date/{attendance_date}")
def read_attendance_by_date_api(
    attendance_date: str,
    current_admin: dict = Depends(require_admin),
):
    attendance = get_attendance_by_date(attendance_date)

    return {
        "status": "success",
        "attendance_date": attendance_date,
        "count": len(attendance),
        "attendance": attendance,
    }


@router.get("/{attendance_id}")
def read_attendance(
    attendance_id: int,
    current_admin: dict = Depends(require_admin),
):
    attendance = get_attendance(attendance_id)

    if attendance is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found.",
        )

    return {
        "status": "success",
        "attendance": attendance,
    }


@router.put("/{attendance_id}")
def update_attendance_api(
    attendance_id: int,
    attendance: AttendanceUpdate,
    current_admin: dict = Depends(require_admin),
):
    existing_attendance = get_attendance(attendance_id)

    if existing_attendance is None:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found.",
        )

    if (
        attendance.status is None
        and attendance.verification_score is None
    ):
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update.",
        )

    try:
        updated = update_attendance(
            attendance_id=attendance_id,
            status=attendance.status,
            verification_score=attendance.verification_score,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found.",
        )

    return {
        "status": "success",
        "message": "Attendance updated successfully.",
        "attendance": get_attendance(attendance_id),
    }