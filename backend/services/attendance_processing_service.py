from backend.services.attendance_service import mark_attendance
from backend.services.verification_attempt_service import (
    VerificationAttemptService,
)
from backend.services.attendance_session_service import get_session
from backend.services.exam_roster_service import is_student_in_exam
from backend.services.student_service import get_student, add_student
from backend.services.holiday_service import check_attendance_allowed
from backend.ai.face_database import FaceDatabase

# High-speed in-memory cache to prevent duplicate MySQL lookups for already marked students
_marked_cache = set()


class AttendanceProcessingService:
    """
    Handles attendance processing after verification.

    Verification itself is handled by VerificationService.

    Flow:

        VerificationService
                ↓
        Verification result
                ↓
        AttendanceProcessingService
                ↓
        Validate attendance session
                ↓
        Validate exam roster
                ↓
        Log verification attempt
                ↓
        Mark attendance
    """

    def __init__(
        self,
        verification_attempt_service=None,
    ):
        self.verification_attempt_service = (
            verification_attempt_service
            or VerificationAttemptService()
        )

    def process_verification(
        self,
        session_id,
        verification,
        attendance_date,
        attendance_time,
        student_name=None,
        status="Present",
    ):
        """
        Process an already completed verification result.

        Attendance is marked only when:
        - the attendance session exists,
        - the attendance session is active,
        - face verification succeeds,
        - the student exists,
        - and the student belongs to the exam roster or matches session class.
        """

        if session_id is None:
            raise ValueError("Session ID cannot be None.")

        if verification is None:
            raise ValueError("Verification result cannot be None.")

        attendance_date = attendance_date.strip()
        attendance_time = attendance_time.strip()

        if not attendance_date:
            raise ValueError("Attendance date cannot be empty.")

        if not attendance_time:
            raise ValueError("Attendance time cannot be empty.")

        # Weekend and Holiday restriction
        is_allowed, block_msg, _ = check_attendance_allowed(attendance_date)
        if not is_allowed:
            return {
                "success": False,
                "verified": False,
                "attendance_marked": False,
                "reason": block_msg,
            }

        # ---------------------------------------------
        # Step 1: Validate attendance session
        # ---------------------------------------------

        session = get_session(session_id)

        if session is None:
            raise ValueError("Attendance session does not exist.")

        if session["ended_at"] is not None:
            raise ValueError("Attendance session has already ended.")

        exam_id = session.get("exam_id")

        # Fast path: If student is already recorded present for this session today, return immediately
        if verification.get("verified"):
            sid = verification.get("student_id")
            if sid and (session_id, sid, attendance_date) in _marked_cache:
                return {
                    "success": False,
                    "verified": True,
                    "attendance_marked": False,
                    "verification_attempt_id": None,
                    "student_id": sid,
                    "student_name": student_name or sid,
                    "similarity": verification.get("similarity"),
                    "liveness_verified": True,
                    "reason": "Attendance already marked for today.",
                }

        # ---------------------------------------------
        # Step 2: Determine verification result
        # ---------------------------------------------

        if verification["verified"]:
            attempt_result = "Success"
            liveness_result = "Verified"
        else:
            attempt_result = "Failed"
            liveness_result = (
                "Verified"
                if verification.get("liveness_verified")
                else "Not Verified"
            )

        # ---------------------------------------------
        # Step 3: Log verification attempt
        # ---------------------------------------------

        attempt_id = (
            self.verification_attempt_service.record_attempt(
                student_id=verification.get("student_id"),
                result=attempt_result,
                similarity=verification.get("similarity"),
                liveness_result=liveness_result,
                reason=verification.get("reason"),
                face_image=verification.get("face_image"),
            )
        )

        # ---------------------------------------------
        # Step 4: Stop if verification failed
        # ---------------------------------------------

        if not verification["verified"]:
            return {
                "success": False,
                "verified": False,
                "attendance_marked": False,
                "verification_attempt_id": attempt_id,
                "student_id": verification.get("student_id"),
                "similarity": verification.get("similarity"),
                "liveness_verified": verification.get(
                    "liveness_verified", False
                ),
                "reason": verification.get("reason", "Face not recognized. Student is not registered."),
            }

        student_id = verification["student_id"]

        # ---------------------------------------------
        # Step 5: Validate student
        # ---------------------------------------------

        student = get_student(student_id)

        # If student exists in face database but record in MySQL was missing, auto-create it
        if student is None:
            face_db = FaceDatabase()
            if face_db.embedding_exists(student_id):
                display_name = (student_name or f"Student {student_id}").strip()
                add_student(student_id=student_id, student_name=display_name)
                student = get_student(student_id)

        if student is None:
            return {
                "success": False,
                "verified": True,
                "attendance_marked": False,
                "verification_attempt_id": attempt_id,
                "student_id": student_id,
                "student_name": student_name,
                "similarity": verification.get("similarity"),
                "liveness_verified": verification.get(
                    "liveness_verified", True
                ),
                "reason": "Recognized student does not exist in student database.",
            }

        # ---------------------------------------------
        # Step 6: Validate class/section match & exam roster (if exam-bound)
        # ---------------------------------------------

        if exam_id is not None:
            from backend.services.exam_service import get_exam
            exam = get_exam(exam_id)
            if exam and exam.get("class_id") and student.get("class_id"):
                if int(exam["class_id"]) != int(student["class_id"]):
                    return {
                        "success": False,
                        "verified": False,
                        "attendance_marked": False,
                        "verification_attempt_id": attempt_id,
                        "student_id": student_id,
                        "student_name": student.get("student_name", student_name),
                        "similarity": verification.get("similarity"),
                        "liveness_verified": verification.get("liveness_verified", True),
                        "reason": "Student belongs to a different section/class. Not enrolled in this session.",
                    }

            if not is_student_in_exam(
                exam_id=exam_id,
                student_id=student_id,
            ):
                from backend.services.exam_roster_service import add_student_to_exam
                try:
                    add_student_to_exam(exam_id=exam_id, student_id=student_id)
                except Exception:
                    pass

        # ---------------------------------------------
        # Step 7: Use authoritative student name
        # ---------------------------------------------

        if student_name is None:
            student_name = student["student_name"]

        student_name = student_name.strip()

        if not student_name:
            raise ValueError(
                "Student name cannot be empty."
            )

        # ---------------------------------------------
        # Step 8: Mark attendance
        # ---------------------------------------------

        attendance_marked = mark_attendance(
            session_id=session_id,
            student_id=student_id,
            student_name=student_name,
            attendance_date=attendance_date,
            attendance_time=attendance_time,
            status=status,
            verification_score=verification.get("similarity"),
            face_image=verification.get("face_image"),
        )

        # ---------------------------------------------
        # Step 9: Attendance successfully marked
        # ---------------------------------------------

        if attendance_marked:
            _marked_cache.add((session_id, student_id, attendance_date))
            return {
                "success": True,
                "verified": True,
                "attendance_marked": True,
                "verification_attempt_id": attempt_id,
                "student_id": student_id,
                "student_name": student_name,
                "similarity": verification.get("similarity"),
                "liveness_verified": verification.get(
                    "liveness_verified", True
                ),
                "reason": "Attendance marked successfully.",
            }

        # ---------------------------------------------
        # Step 10: Duplicate attendance (Already recorded today)
        # ---------------------------------------------

        _marked_cache.add((session_id, student_id, attendance_date))
        return {
            "success": False,
            "verified": True,
            "attendance_marked": False,
            "verification_attempt_id": attempt_id,
            "student_id": student_id,
            "student_name": student_name,
            "similarity": verification.get("similarity"),
            "liveness_verified": verification.get(
                "liveness_verified", True
            ),
            "reason": (
                "Attendance already marked for today."
            ),
        }

    def close(self):
        """
        Close the attendance processing service.
        """
        pass
