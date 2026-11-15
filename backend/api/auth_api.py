from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies import (
    get_bearer_token,
    get_current_user,
    require_admin,
)
from backend.services.auth_service import (
    AuthenticationError,
    DuplicateUserError,
    authenticate_user,
    create_admin_user,
    delete_user_account,
    list_users,
    lookup_student_by_roll_no,
    revoke_token,
    signup_student,
    update_admin_password,
    update_admin_username,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class SignupRequest(BaseModel):
    username: str
    password: str
    full_name: str | None = None
    class_id: int | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class AdminRegisterRequest(BaseModel):
    username: str
    full_name: str
    password: str


@router.get("/student-lookup/{roll_no}")
def student_lookup(roll_no: str):
    """
    Public student verification lookup by Roll No.
    Fetches student details directly from DB records for signup validation.
    """
    try:
        data = lookup_student_by_roll_no(roll_no)
        return {"status": "success", "data": data}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest):
    """
    Public registration endpoint for students.
    - Always assigns role='user'.
    - Username must be the student's unique Roll No.
    - Resolves required student information (name, class) from DB records.
    """
    try:
        user, token = signup_student(
            username=payload.username,
            password=payload.password,
            full_name=payload.full_name,
            class_id=payload.class_id,
        )
    except DuplicateUserError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "status": "success",
        "message": "Student account registered successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/login")
def login(payload: LoginRequest):
    """Authenticate a user (student or admin) using username and password."""
    try:
        user, token = authenticate_user(
            username=payload.username,
            password=payload.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    return {
        "status": "success",
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/logout")
def logout(
    token: str = Depends(get_bearer_token),
    current_user: dict = Depends(get_current_user),
):
    """Invalidate the active JWT token."""
    revoke_token(token)
    return {
        "status": "success",
        "message": "Logged out successfully.",
        "username": current_user["username"],
    }


@router.get("/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user profile (used to restore session on page refresh)."""
    return {
        "status": "success",
        "user": current_user,
    }


@router.post("/admin/register", status_code=status.HTTP_201_CREATED)
def register_admin(
    payload: AdminRegisterRequest,
    current_admin: dict = Depends(require_admin),
):
    """Register a new administrator account. Accessible only to existing admins / system admin."""
    try:
        admin_user = create_admin_user(
            username=payload.username,
            full_name=payload.full_name,
            password=payload.password,
            created_by_username=current_admin["username"],
        )
    except DuplicateUserError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "status": "success",
        "message": f"Administrator '{admin_user['username']}' registered successfully.",
        "user": admin_user,
    }


@router.get("/admins")
def get_admins(current_admin: dict = Depends(require_admin)):
    """List all administrator accounts (admin only)."""
    admins = list_users(role_filter="admin")
    return {
        "status": "success",
        "count": len(admins),
        "admins": admins,
    }


@router.get("/users")
def get_all_users(current_admin: dict = Depends(require_admin)):
    """List all user accounts (admin only)."""
    users = list_users()
    return {
        "status": "success",
        "count": len(users),
        "users": users,
    }


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UpdateUsernameRequest(BaseModel):
    new_username: str
    password: str  # confirm identity


@router.put("/me/password")
def update_my_password(
    payload: UpdatePasswordRequest,
    current_user: dict = Depends(require_admin),
):
    """Allow admin to change their own password."""
    try:
        updated = update_admin_password(
            user_id=current_user["id"],
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"status": "success", "message": "Password updated successfully.", "user": updated}


@router.put("/me/username")
def update_my_username(
    payload: UpdateUsernameRequest,
    current_user: dict = Depends(require_admin),
):
    """Allow admin to change their own username (must be unique)."""
    try:
        updated = update_admin_username(
            user_id=current_user["id"],
            new_username=payload.new_username,
            password=payload.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except DuplicateUserError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"status": "success", "message": "Username updated successfully. Please log in again.", "user": updated}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_admin: dict = Depends(require_admin),
):
    """Delete a non-system-admin user account (admin only)."""
    try:
        deleted = delete_user_account(user_id, current_admin)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return {
        "status": "success",
        "message": "User account deleted successfully.",
        "user_id": user_id,
    }
