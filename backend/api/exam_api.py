from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import require_admin

from backend.services.exam_service import (
    add_exam,
    get_all_exams,
    get_exam,
    get_exams_by_class,
    update_exam,
    delete_exam,
)


router = APIRouter(
    prefix="/exams",
    tags=["Exams"],
    dependencies=[Depends(require_admin)],
)


class ExamCreate(BaseModel):
    exam_name: str
    class_id: int
    exam_date: str
    start_time: str | None = None


class ExamUpdate(BaseModel):
    exam_name: str | None = None
    class_id: int | None = None
    exam_date: str | None = None
    start_time: str | None = None


@router.post("/")
def create_exam(exam: ExamCreate):
    """
    Create a new exam.
    """

    try:
        created = add_exam(
            exam_name=exam.exam_name,
            class_id=exam.class_id,
            exam_date=exam.exam_date,
            start_time=exam.start_time,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if not created:
        raise HTTPException(
            status_code=409,
            detail="Exam could not be created.",
        )

    exams = get_exams_by_class(exam.class_id)

    created_exam = next(
        (
            item
            for item in exams
            if item["exam_name"] == exam.exam_name.strip()
            and item["exam_date"] == exam.exam_date.strip()
        ),
        None,
    )

    return {
        "status": "success",
        "message": "Exam created successfully.",
        "exam": created_exam,
    }


@router.get("/")
def read_exams():
    """
    Get all exams.
    """

    exams = get_all_exams()

    return {
        "status": "success",
        "count": len(exams),
        "exams": exams,
    }


@router.get("/class/{class_id}")
def read_exams_by_class(class_id: int):
    """
    Get all exams belonging to a class.
    """

    exams = get_exams_by_class(class_id)

    return {
        "status": "success",
        "class_id": class_id,
        "count": len(exams),
        "exams": exams,
    }


@router.get("/{exam_id}")
def read_exam(exam_id: int):
    """
    Get a single exam by ID.
    """

    exam = get_exam(exam_id)

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    return {
        "status": "success",
        "exam": exam,
    }


@router.put("/{exam_id}")
def update_exam_api(
    exam_id: int,
    exam: ExamUpdate,
):
    """
    Update an existing exam.
    """

    existing_exam = get_exam(exam_id)

    if existing_exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    if (
        exam.exam_name is None
        and exam.class_id is None
        and exam.exam_date is None
        and exam.start_time is None
    ):
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update.",
        )

    try:
        updated = update_exam(
            exam_id=exam_id,
            exam_name=exam.exam_name,
            class_id=exam.class_id,
            exam_date=exam.exam_date,
            start_time=exam.start_time,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    return {
        "status": "success",
        "message": "Exam updated successfully.",
        "exam": get_exam(exam_id),
    }


@router.delete("/{exam_id}")
def delete_exam_api(exam_id: int):
    """
    Delete an existing exam.
    """

    existing_exam = get_exam(exam_id)

    if existing_exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    deleted = delete_exam(exam_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    return {
        "status": "success",
        "message": "Exam deleted successfully.",
        "exam_id": exam_id,
    }