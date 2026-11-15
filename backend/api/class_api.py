from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import get_current_user, require_admin

from backend.services.class_service import (
    add_class,
    get_all_classes,
    get_class,
    update_class,
    delete_class,
    get_students_by_class,
)


router = APIRouter(
    prefix="/classes",
    tags=["Classes"],
)


class ClassCreate(BaseModel):
    class_name: str
    department: str | None = None
    semester: int | None = None


class ClassUpdate(BaseModel):
    class_name: str | None = None
    department: str | None = None
    semester: int | None = None


@router.post("/")
def create_class(
    class_data: ClassCreate,
    current_admin: dict = Depends(require_admin),
):
    """
    Create a new class (Admin only).
    """

    try:
        created = add_class(
            class_name=class_data.class_name,
            department=class_data.department,
            semester=class_data.semester,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if not created:
        raise HTTPException(
            status_code=409,
            detail="Class already exists.",
        )

    classes = get_all_classes()

    created_class = next(
        (
            item
            for item in classes
            if item["class_name"]
            == class_data.class_name.strip()
        ),
        None,
    )

    return {
        "status": "success",
        "message": "Class created successfully.",
        "class": created_class,
    }


@router.get("/")
def read_classes(current_user: dict = Depends(get_current_user)):
    """
    Get all classes (Authenticated users).
    """

    classes = get_all_classes()

    return {
        "status": "success",
        "count": len(classes),
        "classes": classes,
    }


@router.get("/{class_id}")
def read_class(
    class_id: int,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a single class by ID (Authenticated users).
    """

    class_data = get_class(class_id)

    if class_data is None:
        raise HTTPException(
            status_code=404,
            detail="Class not found.",
        )

    return {
        "status": "success",
        "class": class_data,
    }


@router.put("/{class_id}")
def update_class_api(
    class_id: int,
    class_data: ClassUpdate,
    current_admin: dict = Depends(require_admin),
):
    """
    Update an existing class (Admin only).
    """

    existing_class = get_class(class_id)

    if existing_class is None:
        raise HTTPException(
            status_code=404,
            detail="Class not found.",
        )

    if (
        class_data.class_name is None
        and class_data.department is None
        and class_data.semester is None
    ):
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update.",
        )

    try:
        updated = update_class(
            class_id=class_id,
            class_name=class_data.class_name,
            department=class_data.department,
            semester=class_data.semester,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Class not found.",
        )

    return {
        "status": "success",
        "message": "Class updated successfully.",
        "class": get_class(class_id),
    }


@router.delete("/{class_id}")
def delete_class_api(
    class_id: int,
    current_admin: dict = Depends(require_admin),
):
    """
    Delete an existing class (Admin only).
    """

    existing_class = get_class(class_id)

    if existing_class is None:
        raise HTTPException(
            status_code=404,
            detail="Class not found.",
        )

    deleted = delete_class(class_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Class not found.",
        )

    return {
        "status": "success",
        "message": "Class deleted successfully.",
        "class_id": class_id,
    }


@router.get("/{class_id}/students")
def read_class_students(
    class_id: int,
    current_admin: dict = Depends(require_admin),
):
    """
    Get all students belonging to a class (Admin only).
    """

    existing_class = get_class(class_id)

    if existing_class is None:
        raise HTTPException(
            status_code=404,
            detail="Class not found.",
        )

    students = get_students_by_class(class_id)

    return {
        "status": "success",
        "class_id": class_id,
        "count": len(students),
        "students": students,
    }