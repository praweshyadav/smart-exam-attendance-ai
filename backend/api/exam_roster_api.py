from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import require_admin

from backend.services.exam_roster_service import (
    add_student_to_exam,
    remove_student_from_exam,
    get_exam_roster,
    get_student_exams,
    is_student_in_exam,
    get_exam_roster_count,
    clear_exam_roster,
)

from backend.services.exam_service import get_exam
from backend.services.student_service import get_student


router = APIRouter(
    prefix="/exam-roster",
    tags=["Exam Roster"],
    dependencies=[Depends(require_admin)],
)


class ExamRosterCreate(BaseModel):
    exam_id: int
    student_id: str


@router.post("/")
def add_student_to_exam_api(
    roster: ExamRosterCreate,
):
    exam = get_exam(roster.exam_id)

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    student = get_student(roster.student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    try:
        added = add_student_to_exam(
            exam_id=roster.exam_id,
            student_id=roster.student_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if not added:
        raise HTTPException(
            status_code=409,
            detail="Student is already in this exam roster.",
        )

    roster_data = get_exam_roster(
        roster.exam_id
    )

    created_roster = next(
        (
            item
            for item in roster_data
            if item["student_id"]
            == roster.student_id
        ),
        None,
    )

    return {
        "status": "success",
        "message": "Student added to exam roster successfully.",
        "roster": created_roster,
    }


@router.get("/exam/{exam_id}")
def read_exam_roster(
    exam_id: int,
):
    exam = get_exam(exam_id)

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    roster = get_exam_roster(
        exam_id
    )

    return {
        "status": "success",
        "exam_id": exam_id,
        "count": len(roster),
        "roster": roster,
    }


@router.get("/student/{student_id}")
def read_student_exams(
    student_id: str,
):
    student = get_student(student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    exams = get_student_exams(
        student_id
    )

    return {
        "status": "success",
        "student_id": student_id,
        "count": len(exams),
        "exams": exams,
    }


@router.get("/exam/{exam_id}/count")
def read_exam_roster_count(
    exam_id: int,
):
    exam = get_exam(exam_id)

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    count = get_exam_roster_count(
        exam_id
    )

    return {
        "status": "success",
        "exam_id": exam_id,
        "roster_count": count,
    }


@router.get(
    "/exam/{exam_id}/student/{student_id}"
)
def check_student_exam_roster(
    exam_id: int,
    student_id: str,
):
    exam = get_exam(exam_id)

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    student = get_student(student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    enrolled = is_student_in_exam(
        exam_id=exam_id,
        student_id=student_id,
    )

    return {
        "status": "success",
        "exam_id": exam_id,
        "student_id": student_id,
        "in_roster": enrolled,
    }


@router.delete(
    "/exam/{exam_id}/student/{student_id}"
)
def remove_student_from_exam_api(
    exam_id: int,
    student_id: str,
):
    exam = get_exam(exam_id)

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    student = get_student(student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    removed = remove_student_from_exam(
        exam_id=exam_id,
        student_id=student_id,
    )

    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Student is not in this exam roster.",
        )

    return {
        "status": "success",
        "message": "Student removed from exam roster successfully.",
        "exam_id": exam_id,
        "student_id": student_id,
    }


@router.delete("/exam/{exam_id}")
def clear_exam_roster_api(
    exam_id: int,
):
    exam = get_exam(exam_id)

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found.",
        )

    clear_exam_roster(
        exam_id
    )

    return {
        "status": "success",
        "message": "Exam roster cleared successfully.",
        "exam_id": exam_id,
    }