from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from backend.api.dependencies import (
    ensure_self_or_admin,
    get_current_user,
    require_admin,
)

from backend.services.export_service import (
    # Student
    export_student_report_csv,
    export_student_report_excel,
    export_student_report_pdf,

    # Class
    export_class_report_csv,
    export_class_report_excel,
    export_class_report_pdf,

    # Exam
    export_exam_report_csv,
    export_exam_report_excel,
    export_exam_report_pdf,

    # Daily
    export_daily_report_csv,
    export_daily_report_excel,
    export_daily_report_pdf,
)


router = APIRouter(
    prefix="/exports",
    tags=["Exports"],
)


# ============================================================
# STUDENT EXPORTS
# ============================================================

@router.get("/student/{student_id}/csv")
def export_student_csv(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    ensure_self_or_admin(current_user, student_id)
    try:
        file_path = export_student_report_csv(student_id)

        return FileResponse(
            path=file_path,
            media_type="text/csv",
            filename=f"student_{student_id}_attendance.csv",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get("/student/{student_id}/excel")
def export_student_excel(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    ensure_self_or_admin(current_user, student_id)
    try:
        file_path = export_student_report_excel(student_id)

        return FileResponse(
            path=file_path,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            filename=f"student_{student_id}_attendance.xlsx",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get("/student/{student_id}/pdf")
def export_student_pdf(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    ensure_self_or_admin(current_user, student_id)
    try:
        file_path = export_student_report_pdf(student_id)

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=f"student_{student_id}_attendance.pdf",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# ============================================================
# CLASS EXPORTS
# ============================================================

@router.get("/class/{class_id}/csv")
def export_class_csv(
    class_id: int,
    current_admin: dict = Depends(require_admin),
):
    try:
        file_path = export_class_report_csv(class_id)

        return FileResponse(
            path=file_path,
            media_type="text/csv",
            filename=f"class_{class_id}_attendance.csv",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get("/class/{class_id}/excel")
def export_class_excel(
    class_id: int,
    current_admin: dict = Depends(require_admin),
):
    try:
        file_path = export_class_report_excel(class_id)

        return FileResponse(
            path=file_path,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            filename=f"class_{class_id}_attendance.xlsx",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get("/class/{class_id}/pdf")
def export_class_pdf(
    class_id: int,
    current_admin: dict = Depends(require_admin),
):
    try:
        file_path = export_class_report_pdf(class_id)

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=f"class_{class_id}_attendance.pdf",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# ============================================================
# EXAM EXPORTS
# ============================================================

@router.get("/exam/{exam_id}/csv")
def export_exam_csv(
    exam_id: int,
    current_admin: dict = Depends(require_admin),
):
    try:
        file_path = export_exam_report_csv(exam_id)

        return FileResponse(
            path=file_path,
            media_type="text/csv",
            filename=f"exam_{exam_id}_attendance.csv",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get("/exam/{exam_id}/excel")
def export_exam_excel(
    exam_id: int,
    current_admin: dict = Depends(require_admin),
):
    try:
        file_path = export_exam_report_excel(exam_id)

        return FileResponse(
            path=file_path,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            filename=f"exam_{exam_id}_attendance.xlsx",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get("/exam/{exam_id}/pdf")
def export_exam_pdf(
    exam_id: int,
    current_admin: dict = Depends(require_admin),
):
    try:
        file_path = export_exam_report_pdf(exam_id)

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=f"exam_{exam_id}_attendance.pdf",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# ============================================================
# DAILY EXPORTS
# ============================================================

@router.get("/daily/{attendance_date}/csv")
def export_daily_csv(
    attendance_date: str,
    current_admin: dict = Depends(require_admin),
):
    try:
        file_path = export_daily_report_csv(attendance_date)

        return FileResponse(
            path=file_path,
            media_type="text/csv",
            filename=f"daily_attendance_{attendance_date}.csv",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get("/daily/{attendance_date}/excel")
def export_daily_excel(
    attendance_date: str,
    current_admin: dict = Depends(require_admin),
):
    try:
        file_path = export_daily_report_excel(attendance_date)

        return FileResponse(
            path=file_path,
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            filename=f"daily_attendance_{attendance_date}.xlsx",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get("/daily/{attendance_date}/pdf")
def export_daily_pdf(
    attendance_date: str,
    current_admin: dict = Depends(require_admin),
):
    try:
        file_path = export_daily_report_pdf(attendance_date)

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=f"daily_attendance_{attendance_date}.pdf",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )