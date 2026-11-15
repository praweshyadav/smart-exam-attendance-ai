import os
import secrets
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Main directories
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = DATA_DIR / "exports"
LOG_DIR = BASE_DIR / "logs"

# AI data
AI_DATA_DIR = DATA_DIR / "ai"

# Face recognition data
FACE_DATABASE_PATH = AI_DATA_DIR / "face_database.pkl"

# Model paths
FACE_LANDMARKER_PATH = BASE_DIR / "face_landmarker.task"

# Create required directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
AI_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Face recognition configuration
FACE_RECOGNITION_THRESHOLD = float(os.getenv("FACE_RECOGNITION_THRESHOLD", "0.55"))

# Liveness & Anti-Spoofing configuration (strictly enabled by default)
LIVENESS_ENABLED = os.getenv("LIVENESS_ENABLED", "true").lower() in ("true", "1", "yes")
BLINK_THRESHOLD = float(os.getenv("BLINK_THRESHOLD", "0.24"))
MIN_CLOSED_FRAMES = int(os.getenv("MIN_CLOSED_FRAMES", "1"))
CHALLENGE_STEP_TIMEOUT_SECONDS = float(os.getenv("CHALLENGE_STEP_TIMEOUT_SECONDS", "15.0"))

# Weekend Attendance Policy (Set to False to allow verification and testing on weekends)
ENABLE_WEEKEND_RESTRICTION = os.getenv("ENABLE_WEEKEND_RESTRICTION", "false").lower() in ("true", "1", "yes")

# Authentication & Authorization configuration
def _load_or_create_secret():
    env_secret = os.getenv("AUTH_SECRET_KEY")
    if env_secret:
        return env_secret
    secret_file = DATA_DIR / ".auth_secret"
    if secret_file.exists():
        try:
            val = secret_file.read_text(encoding="utf-8").strip()
            if len(val) >= 32:
                return val
        except Exception:
            pass
    new_secret = secrets.token_hex(32)
    try:
        secret_file.write_text(new_secret, encoding="utf-8")
    except Exception:
        pass
    return new_secret

AUTH_SECRET_KEY = _load_or_create_secret()
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
SYSTEM_ADMIN_USERNAME = os.getenv("SYSTEM_ADMIN_USERNAME", "admin")
# SYSTEM_ADMIN_PASSWORD = os.getenv("SYSTEM_ADMIN_PASSWORD", "Admin@123")
SYSTEM_ADMIN_PASSWORD = os.getenv("SYSTEM_ADMIN_PASSWORD")
if not SYSTEM_ADMIN_PASSWORD:
    raise RuntimeError("SYSTEM_ADMIN_PASSWORD environment variable is required")
SYSTEM_ADMIN_FULL_NAME = os.getenv("SYSTEM_ADMIN_FULL_NAME", "System Administrator")
