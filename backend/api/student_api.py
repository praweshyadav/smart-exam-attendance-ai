from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import (
    ensure_self_or_admin,
    get_current_user,
    require_admin,
)

from backend.services.student_service import (
    add_student,
    get_all_students,
    get_student,
    update_student,
    delete_student,
)

from backend.services.class_service import (
    class_exists,
)


router = APIRouter(
    prefix="/students",
    tags=["Students"],
)


class StudentCreate(BaseModel):
    student_id: str
    student_name: str
    class_id: int | None = None


class StudentUpdate(BaseModel):
    student_name: str | None = None
    class_id: int | None = None


@router.post("/")
def create_student(
    student: StudentCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new student (Admin for any student, or Student for their own Roll No).
    """
    ensure_self_or_admin(current_user, student.student_id)

    if student.class_id is not None:
        if not class_exists(student.class_id):
            raise HTTPException(
                status_code=400,
                detail="Class does not exist.",
            )

    try:
        created = add_student(
            student_id=student.student_id,
            student_name=student.student_name,
            class_id=student.class_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if not created:
        raise HTTPException(
            status_code=409,
            detail="Student already exists.",
        )

    return {
        "status": "success",
        "message": "Student created successfully.",
        "student": get_student(
            student.student_id
        ),
    }


@router.get("/")
def read_students(current_admin: dict = Depends(require_admin)):
    """
    Get all students (Admin only).
    """

    students = get_all_students()

    return {
        "status": "success",
        "count": len(students),
        "students": students,
    }


@router.get("/{student_id}")
def read_student(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a single student by student ID (Admin or self).
    """
    ensure_self_or_admin(current_user, student_id)

    student = get_student(student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    return {
        "status": "success",
        "student": student,
    }


@router.put("/{student_id}")
def update_student_api(
    student_id: str,
    student: StudentUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update an existing student (Admin or self).
    """
    ensure_self_or_admin(current_user, student_id)

    existing_student = get_student(
        student_id
    )

    if existing_student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    if student.class_id is not None:
        if not class_exists(student.class_id):
            raise HTTPException(
                status_code=400,
                detail="Class does not exist.",
            )

    if (
        student.student_name is None
        and student.class_id is None
    ):
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update.",
        )

    try:
        updated = update_student(
            student_id=student_id,
            student_name=student.student_name,
            class_id=student.class_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    return {
        "status": "success",
        "message": "Student updated successfully.",
        "student": get_student(
            student_id
        ),
    }


@router.delete("/{student_id}")
def delete_student_api(
    student_id: str,
    current_admin: dict = Depends(require_admin),
):
    """
    Delete an existing student (Admin only).
    """

    existing_student = get_student(
        student_id
    )

    if existing_student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    deleted = delete_student(
        student_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Student not found.",
        )

    return {
        "status": "success",
        "message": "Student deleted successfully.",
        "student_id": student_id,
    }