from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.dependencies import require_admin
from backend.services.verification_attempt_service import (
    VerificationAttemptService,
)


router = APIRouter(
    prefix="/verification-attempts",
    tags=["Verification Attempts"],
    dependencies=[Depends(require_admin)],
)


verification_service = VerificationAttemptService()


class VerificationAttemptCreate(BaseModel):
    student_id: str | None = None
    result: str
    similarity: float | None = None
    liveness_result: str | None = None
    reason: str | None = None


@router.post("/")
def create_verification_attempt(
    attempt: VerificationAttemptCreate,
):
    try:
        attempt_id = verification_service.record_attempt(
            student_id=attempt.student_id,
            result=attempt.result,
            similarity=attempt.similarity,
            liveness_result=attempt.liveness_result,
            reason=attempt.reason,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "status": "success",
        "message": "Verification attempt logged successfully.",
        "attempt": verification_service.get_attempt(
            attempt_id
        ),
    }


@router.get("/")
def read_all_verification_attempts():
    attempts = verification_service.get_all_attempts()

    return {
        "status": "success",
        "count": len(attempts),
        "attempts": attempts,
    }


@router.get("/student/{student_id}")
def read_attempts_by_student(student_id: str):
    attempts = verification_service.get_attempts_by_student(
        student_id
    )

    return {
        "status": "success",
        "student_id": student_id,
        "count": len(attempts),
        "attempts": attempts,
    }


@router.get("/result/{result}")
def read_attempts_by_result(result: str):
    try:
        attempts = verification_service.get_attempts_by_result(
            result
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "status": "success",
        "result": result,
        "count": len(attempts),
        "attempts": attempts,
    }


@router.get("/{attempt_id}")
def read_verification_attempt(attempt_id: int):
    attempt = verification_service.get_attempt(
        attempt_id
    )

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Verification attempt not found.",
        )

    return {
        "status": "success",
        "attempt": attempt,
    }


@router.delete("/{attempt_id}")
def delete_verification_attempt(attempt_id: int):
    attempt = verification_service.get_attempt(
        attempt_id
    )

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Verification attempt not found.",
        )

    deleted = verification_service.delete_attempt(
        attempt_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Verification attempt not found.",
        )

    return {
        "status": "success",
        "message": "Verification attempt deleted successfully.",
        "attempt_id": attempt_id,
    }