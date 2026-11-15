from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.database import initialize_database
from backend.api.auth_api import router as auth_router
from backend.api.student_api import router as student_router
from backend.api.class_api import router as class_router
from backend.api.exam_api import router as exam_router
from backend.api.attendance_session_api import router as attendance_session_router
from backend.api.attendance_api import router as attendance_router
from backend.api.verification_attempt_api import router as verification_attempt_router
from backend.api.face_registration_api import router as face_registration_router
from backend.api.verification_api import router as verification_router
from backend.api.attendance_verification_api import router as attendance_verification_router
from backend.api.attendance_verification_session_api import router as attendance_verification_session_router
from backend.api.exam_roster_api import router as exam_roster_router
from backend.api.analytics_api import router as analytics_router
from backend.api.export_router import router as export_router
from backend.api.dashboard_api import router as dashboard_router

app = FastAPI(
    title="Smart Exam Attendance API",
    description="Backend API for the Smart Exam Attendance System",
    version="1.0.0",
)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    try:
        initialize_database()
    except Exception as err:
        print(f"Warning: Database auto-initialization error: {err}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(student_router)
app.include_router(class_router)
app.include_router(exam_router)
app.include_router(attendance_session_router)
app.include_router(attendance_router)
app.include_router(verification_attempt_router)
app.include_router(face_registration_router)
app.include_router(verification_router)
app.include_router(attendance_verification_router)
app.include_router(attendance_verification_session_router)
app.include_router(exam_roster_router)
app.include_router(analytics_router)
app.include_router(export_router)
app.include_router(dashboard_router)
app.include_router(dashboard_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Smart Exam Attendance API is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }
