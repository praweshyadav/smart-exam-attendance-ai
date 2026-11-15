import base64
import datetime
import hashlib
import hmac
import json
import re
import secrets
import time
from uuid import uuid4

from backend.core.config import ACCESS_TOKEN_EXPIRE_HOURS, AUTH_SECRET_KEY
from backend.database.database import get_connection
from backend.services.activity_service import log_activity


ROLL_NO_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,50}$")
ADMIN_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")


class DuplicateUserError(ValueError):
    """Raised when attempting to register a username/roll number that already exists."""


class AuthenticationError(ValueError):
    """Raised when login credentials or token validation fail."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    salt = secrets.token_bytes(16)
    iterations = 200_000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2-HMAC-SHA256 hash."""
    if not password or not stored_hash:
        return False
    try:
        scheme, iter_str, salt_hex, hash_hex = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except Exception:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected)


def _sanitize_user(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
        "is_system_admin": bool(row.get("is_system_admin")),
        "student_id": row.get("student_id"),
        "created_by": row.get("created_by"),
        "is_active": bool(row.get("is_active", 1)),
        "created_at": row.get("created_at"),
    }


def create_access_token(user: dict, expires_hours: int | None = None) -> str:
    """Create a signed HS256 JWT access token for an authenticated user."""
    now = int(time.time())
    ttl_hours = expires_hours if expires_hours is not None else ACCESS_TOKEN_EXPIRE_HOURS
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "is_system_admin": bool(user.get("is_system_admin")),
        "jti": uuid4().hex,
        "iat": now,
        "exp": now + int(ttl_hours * 3600),
    }
    h_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{h_b64}.{p_b64}".encode("ascii")
    sig = hmac.new(AUTH_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{h_b64}.{p_b64}.{_b64url_encode(sig)}"


def decode_access_token(token: str) -> dict:
    """Verify JWT signature, expiry, and revocation status, returning its payload."""
    if not token or not isinstance(token, str):
        raise AuthenticationError("Missing authentication token.")
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise AuthenticationError("Invalid authentication token format.")

    h_b64, p_b64, s_b64 = parts
    signing_input = f"{h_b64}.{p_b64}".encode("ascii")
    expected_sig = hmac.new(AUTH_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        actual_sig = _b64url_decode(s_b64)
        if not hmac.compare_digest(actual_sig, expected_sig):
            raise AuthenticationError("Invalid authentication token signature.")
        payload = json.loads(_b64url_decode(p_b64).decode("utf-8"))
    except AuthenticationError:
        raise
    except Exception:
        raise AuthenticationError("Malformed authentication token.")

    now = int(time.time())
    if int(payload.get("exp", 0)) < now:
        raise AuthenticationError("Authentication token has expired.")

    jti = payload.get("jti")
    if jti:
        with get_connection() as conn:
            revoked = conn.execute(
                "SELECT jti FROM revoked_tokens WHERE jti = ? LIMIT 1",
                (jti,),
            ).fetchone()
            if revoked:
                raise AuthenticationError("Session has been logged out. Please log in again.")

    return payload


def revoke_token(token: str) -> None:
    """Revoke a JWT token so it can no longer be used after logout."""
    try:
        payload = decode_access_token(token)
    except AuthenticationError:
        return
    jti = payload.get("jti")
    exp = int(payload.get("exp", int(time.time()) + 3600))
    if not jti:
        return
    exp_dt = datetime.datetime.fromtimestamp(exp).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "INSERT IGNORE INTO revoked_tokens (jti, expires_at) VALUES (?, ?)",
            (jti, exp_dt),
        )
        conn.execute("DELETE FROM revoked_tokens WHERE expires_at < NOW()")
        conn.commit()


def get_user_by_id(user_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, username, full_name, role, is_system_admin, student_id, created_by, is_active, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    return _sanitize_user(dict(row)) if row else None


def get_user_by_username(username: str) -> dict | None:
    if not username:
        return None
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, username, full_name, role, is_system_admin, student_id, created_by, is_active, created_at
            FROM users
            WHERE username = ?
            """,
            (username.strip(),),
        ).fetchone()
    return _sanitize_user(dict(row)) if row else None


def lookup_student_by_roll_no(roll_no: str) -> dict:
    """
    Lookup student profile by roll number from DB records for pre-signup validation.
    """
    roll_no = (roll_no or "").strip()
    if not roll_no:
        raise ValueError("Roll number cannot be empty.")

    with get_connection() as conn:
        existing_user = conn.execute(
            "SELECT id, username FROM users WHERE LOWER(username) = LOWER(?) LIMIT 1",
            (roll_no,),
        ).fetchone()
        if existing_user:
            return {
                "found": True,
                "already_registered": True,
                "message": "An account for this roll number already exists. Please log in.",
            }

        student = conn.execute(
            """
            SELECT
                s.student_id,
                s.student_name,
                s.class_id,
                c.class_name,
                c.department,
                c.semester
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.class_id
            WHERE s.student_id = ?
            LIMIT 1
            """,
            (roll_no,),
        ).fetchone()

        if not student:
            return {
                "found": False,
                "already_registered": False,
                "message": f"Roll number '{roll_no}' was not found in student records. Please contact your administrator.",
            }

        return {
            "found": True,
            "already_registered": False,
            "student_id": student["student_id"],
            "student_name": student["student_name"],
            "class_name": student.get("class_name") or "",
            "department": student.get("department") or "",
            "semester": student.get("semester") or "",
        }


def signup_student(
    username: str,
    password: str,
    full_name: str | None = None,
    class_id: int | None = None,
) -> tuple[dict, str]:
    """
    Public student self-registration.
    - Role is ALWAYS forced to 'user' (never admin).
    - Username MUST be the student's unique Roll No.
    - Resolves student details (student_name, class_id) directly from the `students` DB record.
    """
    roll_no = (username or "").strip()
    if not roll_no or not ROLL_NO_PATTERN.match(roll_no):
        raise ValueError(
            "Roll number (username) must be 3-50 characters using letters, numbers, '-' or '_' only."
        )

    pw_hash = hash_password(password)

    with get_connection() as conn:
        existing_user = conn.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(?) LIMIT 1",
            (roll_no,),
        ).fetchone()
        if existing_user:
            raise DuplicateUserError("An account with this roll number already exists. Please log in.")

        existing_student = conn.execute(
            """
            SELECT s.student_id, s.student_name, s.class_id, c.class_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.class_id
            WHERE s.student_id = ?
            LIMIT 1
            """,
            (roll_no,),
        ).fetchone()

        if existing_student is None:
            if full_name and full_name.strip():
                resolved_name = full_name.strip()
                conn.execute(
                    """
                    INSERT INTO students (student_id, student_name, class_id, face_registered)
                    VALUES (?, ?, ?, 0)
                    """,
                    (roll_no, resolved_name, class_id),
                )
            else:
                raise ValueError(
                    f"Roll number '{roll_no}' was not found in student records. Please contact your administrator to be enrolled before creating an account."
                )
        else:
            resolved_name = existing_student["student_name"]
            if class_id is None:
                class_id = existing_student.get("class_id")

        cursor = conn.execute(
            """
            INSERT INTO users (username, full_name, password_hash, role, is_system_admin, student_id, created_by, is_active)
            VALUES (?, ?, ?, 'user', 0, ?, 'self', 1)
            """,
            (roll_no, resolved_name, pw_hash, roll_no),
        )
        conn.commit()
        user_id = cursor.lastrowid

    from backend.services.student_service import _invalidate_student_cache
    _invalidate_student_cache(roll_no)

    user = get_user_by_id(user_id)
    token = create_access_token(user)
    log_activity("USER_SIGNUP", f"Student account created: {resolved_name} ({roll_no})", "user", roll_no)
    return user, token


def authenticate_user(username: str, password: str) -> tuple[dict, str]:
    """Verify username and password and issue a signed JWT token."""
    uname = (username or "").strip()
    if not uname or not password:
        raise AuthenticationError("Username and password are required.")

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, username, full_name, password_hash, role, is_system_admin, student_id, created_by, is_active, created_at
            FROM users
            WHERE username = ?
            LIMIT 1
            """,
            (uname,),
        ).fetchone()

    if not row or not verify_password(password, row["password_hash"]):
        raise AuthenticationError("Invalid username or password.")

    if not row.get("is_active", 1):
        raise AuthenticationError("Account is deactivated. Contact an administrator.")

    user = _sanitize_user(dict(row))
    token = create_access_token(user)
    return user, token


def create_admin_user(
    username: str,
    full_name: str,
    password: str,
    created_by_username: str,
) -> dict:
    """
    Create a new administrator account.
    Caller must already be verified as an authenticated admin or system admin.
    """
    uname = (username or "").strip()
    name = (full_name or "").strip()

    if not uname or not ADMIN_USERNAME_PATTERN.match(uname):
        raise ValueError(
            "Admin username must be 3-50 characters using letters, numbers, '.', '-' or '_'."
        )
    if not name:
        raise ValueError("Full name cannot be empty.")

    pw_hash = hash_password(password)

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(?) LIMIT 1",
            (uname,),
        ).fetchone()
        if existing:
            raise DuplicateUserError("Username already exists.")

        cursor = conn.execute(
            """
            INSERT INTO users (username, full_name, password_hash, role, is_system_admin, student_id, created_by, is_active)
            VALUES (?, ?, ?, 'admin', 0, NULL, ?, 1)
            """,
            (uname, name, pw_hash, created_by_username),
        )
        conn.commit()
        user_id = cursor.lastrowid

    log_activity(
        "ADMIN_CREATED",
        f"New admin '{uname}' registered by {created_by_username}",
        "user",
        uname,
    )
    return get_user_by_id(user_id)


def list_users(role_filter: str | None = None) -> list[dict]:
    with get_connection() as conn:
        if role_filter:
            rows = conn.execute(
                """
                SELECT id, username, full_name, role, is_system_admin, student_id, created_by, is_active, created_at
                FROM users
                WHERE role = ?
                ORDER BY is_system_admin DESC, created_at DESC
                """,
                (role_filter,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, username, full_name, role, is_system_admin, student_id, created_by, is_active, created_at
                FROM users
                ORDER BY role ASC, is_system_admin DESC, created_at DESC
                """
            ).fetchall()
    return [_sanitize_user(dict(r)) for r in rows]


def update_admin_password(user_id: int, current_password: str, new_password: str) -> dict:
    """Update admin's own password after verifying current password."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, full_name, password_hash, role, is_system_admin, student_id, created_by, is_active, created_at FROM users WHERE id = ? LIMIT 1",
            (user_id,),
        ).fetchone()
    if not row:
        raise AuthenticationError("User not found.")
    if not verify_password(current_password, row["password_hash"]):
        raise AuthenticationError("Current password is incorrect.")
    new_hash = hash_password(new_password)
    with get_connection() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        conn.commit()
    log_activity("PASSWORD_CHANGED", f"Admin '{row['username']}' changed their password", "user", row["username"])
    return _sanitize_user(dict(row))


def update_admin_username(user_id: int, new_username: str, password: str) -> dict:
    """Update admin's own username after verifying password. Username must be unique."""
    uname = (new_username or "").strip()
    if not uname or not ADMIN_USERNAME_PATTERN.match(uname):
        raise ValueError("Username must be 3-50 characters using letters, numbers, '.', '-' or '_'.")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, full_name, password_hash, role, is_system_admin, student_id, created_by, is_active, created_at FROM users WHERE id = ? LIMIT 1",
            (user_id,),
        ).fetchone()
        if not row:
            raise AuthenticationError("User not found.")
        if not verify_password(password, row["password_hash"]):
            raise AuthenticationError("Password is incorrect.")
        existing = conn.execute(
            "SELECT id FROM users WHERE LOWER(username) = LOWER(?) AND id != ? LIMIT 1",
            (uname, user_id),
        ).fetchone()
        if existing:
            raise DuplicateUserError("Username already taken. Please choose a different username.")
        conn.execute("UPDATE users SET username = ? WHERE id = ?", (uname, user_id))
        conn.commit()
    log_activity("USERNAME_CHANGED", f"Admin changed username to '{uname}'", "user", uname)
    return get_user_by_id(user_id)


def delete_user_account(target_user_id: int, actor_user: dict) -> bool:
    """Delete a non-system-admin user account."""
    if int(target_user_id) == int(actor_user["id"]):
        raise ValueError("You cannot delete your own currently logged-in account.")

    with get_connection() as conn:
        target = conn.execute(
            "SELECT id, username, role, is_system_admin FROM users WHERE id = ? LIMIT 1",
            (target_user_id,),
        ).fetchone()
        if not target:
            return False
        if target.get("is_system_admin"):
            raise ValueError("The primary System Admin account cannot be deleted.")

        conn.execute("DELETE FROM users WHERE id = ?", (target_user_id,))
        conn.commit()

    log_activity(
        "USER_DELETED",
        f"User '{target['username']}' ({target['role']}) deleted by {actor_user['username']}",
        "user",
        target["username"],
    )
    return True
