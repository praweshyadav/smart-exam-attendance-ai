from fastapi import APIRouter, Depends

from backend.api.dependencies import (
    ensure_self_or_admin,
    get_current_user,
    require_admin,
)
from backend.services.analytics_service import (
    get_overall_attendance,
    get_student_attendance,
    get_all_student_attendance,
    get_class_attendance,
    get_exam_attendance,
    get_daily_attendance,
    get_attendance_by_date_range,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/overall")
def read_overall_attendance(current_admin: dict = Depends(require_admin)):
    data = get_overall_attendance()
    return {
        **data,
        "status": "success",
        "analytics": data,
    }


@router.get("/students")
def read_all_student_attendance(current_admin: dict = Depends(require_admin)):
    return get_all_student_attendance()


@router.get("/student/{student_id}")
def read_student_attendance(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    ensure_self_or_admin(current_user, student_id)
    data = get_student_attendance(student_id)
    return {
        **data,
        "status": "success",
        "analytics": data,
    }


@router.get("/class/{class_id}")
def read_class_attendance(
    class_id: int,
    current_admin: dict = Depends(require_admin),
):
    data = get_class_attendance(class_id)
    return {
        **data,
        "status": "success",
        "analytics": data,
    }


@router.get("/exam/{exam_id}")
def read_exam_attendance(
    exam_id: int,
    current_admin: dict = Depends(require_admin),
):
    data = get_exam_attendance(exam_id)
    return {
        **data,
        "status": "success",
        "analytics": data,
    }


@router.get("/daily/{attendance_date}")
def read_daily_attendance(
    attendance_date: str,
    current_admin: dict = Depends(require_admin),
):
    data = get_daily_attendance(attendance_date)
    return {
        **data,
        "status": "success",
        "analytics": data,
    }


@router.get("/range")
def read_attendance_by_date_range(
    start_date: str,
    end_date: str,
    current_admin: dict = Depends(require_admin),
):
    return get_attendance_by_date_range(
        start_date,
        end_date,
    )
