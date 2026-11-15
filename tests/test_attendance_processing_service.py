import sys
import os
sys.path.insert(0, os.path.abspath("."))

from backend.database.database import get_connection
from backend.services.attendance_processing_service import (
    AttendanceProcessingService,
)
from backend.services.attendance_service import (
    get_attendance_by_session,
)
from backend.services.attendance_session_service import (
    start_session,
    end_session,
)
from backend.services.exam_service import (
    add_exam,
)
from backend.services.class_service import (
    add_class,
)
from backend.services.student_service import (
    add_student,
    delete_student,
)
from backend.services.verification_attempt_service import (
    VerificationAttemptService,
)


print("===== ATTENDANCE PROCESSING SERVICE TEST =====")

TEST_STUDENT_ID = "TEST_ATTENDANCE_001"
TEST_STUDENT_NAME = "Test Attendance Student"
TEST_CLASS_NAME = "Test Attendance Class"
TEST_EXAM_NAME = "Test Attendance Exam"


class FakeVerificationAttemptService:
    """
    Fake attempt service used to verify that
    AttendanceProcessingService sends the correct
    verification information.
    """

    def __init__(self):
        self.attempts = []
        self.next_id = 1

    def record_attempt(
        self,
        student_id=None,
        result="Failed",
        similarity=None,
        liveness_result=None,
        reason=None,
    ):
        attempt = {
            "id": self.next_id,
            "student_id": student_id,
            "result": result,
            "similarity": similarity,
            "liveness_result": liveness_result,
            "reason": reason,
        }
        self.attempts.append(attempt)
        self.next_id += 1
        return attempt["id"]


# -------------------------------------------------
# Setup & Cleanup previous test data
# -------------------------------------------------

print("1. Cleaning previous test data...")

delete_student(TEST_STUDENT_ID)

with get_connection() as connection:
    connection.execute(
        """
        DELETE FROM verification_attempts
        WHERE student_id = ?
        """,
        (TEST_STUDENT_ID,),
    )
    connection.execute(
        """
        DELETE FROM attendance
        WHERE student_id = ?
        """,
        (TEST_STUDENT_ID,),
    )
    connection.commit()

print("   PASS")


# -------------------------------------------------
# Create class
# -------------------------------------------------

print("2. Creating temporary test class...")

with get_connection() as connection:
    existing_class = connection.execute(
        """
        SELECT class_id
        FROM classes
        WHERE class_name = ?
        """,
        (TEST_CLASS_NAME,),
    ).fetchone()

if existing_class:
    class_id = existing_class["class_id"]
else:
    add_class(
        TEST_CLASS_NAME,
        "TEST",
        1,
    )
    with get_connection() as connection:
        class_row = connection.execute(
            """
            SELECT class_id
            FROM classes
            WHERE class_name = ?
            """,
            (TEST_CLASS_NAME,),
        ).fetchone()
        class_id = class_row["class_id"]

print(f"   Class ID: {class_id}")
print("   PASS")


# -------------------------------------------------
# Create student
# -------------------------------------------------

print("3. Creating temporary test student...")

created = add_student(
    TEST_STUDENT_ID,
    TEST_STUDENT_NAME,
    class_id,
)

if not created:
    raise RuntimeError("Temporary test student could not be created.")

print("   PASS")


# -------------------------------------------------
# Create exam
# -------------------------------------------------

print("4. Creating temporary test exam...")

add_exam(
    TEST_EXAM_NAME,
    class_id,
    "2026-09-08",
    "10:00",
)

with get_connection() as connection:
    exam_row = connection.execute(
        """
        SELECT exam_id
        FROM exams
        WHERE exam_name = ?
        ORDER BY exam_id DESC
        LIMIT 1
        """,
        (TEST_EXAM_NAME,),
    ).fetchone()
    exam_id = exam_row["exam_id"]

print(f"   Exam ID: {exam_id}")
print("   PASS")


# -------------------------------------------------
# Create attendance session
# -------------------------------------------------

print("5. Starting attendance session...")

session_id = start_session(exam_id)

print(f"   Session ID: {session_id}")
print("   PASS")


# -------------------------------------------------
# Initialize service with fake attempt logger
# -------------------------------------------------

print("6. Creating attendance processing service...")

fake_attempt_service = FakeVerificationAttemptService()
service = AttendanceProcessingService(
    verification_attempt_service=fake_attempt_service,
)

print("   PASS")


# -------------------------------------------------
# Test 1: Successful verification processing
# -------------------------------------------------

print("7. Testing successful attendance processing...")

successful_verification = {
    "verified": True,
    "student_id": TEST_STUDENT_ID,
    "similarity": 0.88,
    "face_detected": True,
    "face_matched": True,
    "liveness_verified": True,
    "reason": "Student verified successfully.",
}

result = service.process_verification(
    session_id=session_id,
    verification=successful_verification,
    attendance_date="2026-09-08",
    attendance_time="10:05:00",
    student_name=TEST_STUDENT_NAME,
)

print(f"   Verified: {result['verified']}")
print(f"   Attendance marked: {result['attendance_marked']}")
print(f"   Student ID: {result['student_id']}")
print(f"   Similarity: {result['similarity']}")
print(f"   Reason: {result['reason']}")

if not result["success"]:
    raise RuntimeError("Successful verification should return success.")

if not result["verified"]:
    raise RuntimeError("Student should be verified.")

if not result["attendance_marked"]:
    raise RuntimeError("Attendance should be marked.")

if result["student_id"] != TEST_STUDENT_ID:
    raise RuntimeError("Incorrect student ID.")

if result["similarity"] != 0.88:
    raise RuntimeError("Incorrect similarity.")

print("   PASS")


# -------------------------------------------------
# Test 2: Verify database attendance
# -------------------------------------------------

print("8. Checking attendance database...")

attendance_records = get_attendance_by_session(session_id)

print(f"   Attendance records: {len(attendance_records)}")

if len(attendance_records) != 1:
    raise RuntimeError("Exactly one attendance record should exist.")

attendance = attendance_records[0]

if attendance["student_id"] != TEST_STUDENT_ID:
    raise RuntimeError("Incorrect student in attendance record.")

if attendance["status"] != "Present":
    raise RuntimeError("Attendance status should be Present.")

if attendance["verification_score"] != 0.88:
    raise RuntimeError("Incorrect verification score.")

print("   PASS")


# -------------------------------------------------
# Test 3: Duplicate attendance protection
# -------------------------------------------------

print("9. Testing duplicate attendance protection...")

result = service.process_verification(
    session_id=session_id,
    verification=successful_verification,
    attendance_date="2026-09-08",
    attendance_time="10:06:00",
    student_name=TEST_STUDENT_NAME,
)

print(f"   Attendance marked: {result['attendance_marked']}")
print(f"   Reason: {result['reason']}")

if result["attendance_marked"]:
    raise RuntimeError("Duplicate attendance must not be marked.")

if "already marked" not in result["reason"]:
    raise RuntimeError("Incorrect duplicate attendance reason.")

attendance_records = get_attendance_by_session(session_id)

if len(attendance_records) != 1:
    raise RuntimeError("Duplicate attendance record was created.")

print("   PASS")


# -------------------------------------------------
# Test 4: Failed verification
# -------------------------------------------------

print("10. Testing failed verification...")

failed_verification = {
    "verified": False,
    "student_id": None,
    "similarity": 0.32,
    "face_detected": True,
    "face_matched": False,
    "liveness_verified": False,
    "reason": "Face not recognized.",
}

result = service.process_verification(
    session_id=session_id,
    verification=failed_verification,
    attendance_date="2026-09-08",
    attendance_time="10:07:00",
    student_name=TEST_STUDENT_NAME,
)

print(f"   Verified: {result['verified']}")
print(f"   Attendance marked: {result['attendance_marked']}")
print(f"   Reason: {result['reason']}")

if result["verified"]:
    raise RuntimeError("Failed verification should not be verified.")

if result["attendance_marked"]:
    raise RuntimeError("Attendance must not be marked after failed verification.")

print("   PASS")


# -------------------------------------------------
# Test 5: Verify attempts logging
# -------------------------------------------------

print("11. Checking verification attempt logging...")

if len(fake_attempt_service.attempts) != 3:
    raise RuntimeError(
        f"Expected 3 attempts logged, got {len(fake_attempt_service.attempts)}"
    )

last_attempt = fake_attempt_service.attempts[-1]

if last_attempt["result"] != "Failed":
    raise RuntimeError("Failed verification should be logged as Failed.")

if last_attempt["reason"] != "Face not recognized.":
    raise RuntimeError("Incorrect failure reason logged.")

print("   PASS")


# -------------------------------------------------
# Test 6: Close service
# -------------------------------------------------

print("12. Testing resource cleanup...")

service.close()

print("   PASS")


# -------------------------------------------------
# End session
# -------------------------------------------------

print("13. Ending attendance session...")

ended = end_session(session_id)

if not ended:
    raise RuntimeError("Attendance session could not be ended.")

print("   PASS")


# -------------------------------------------------
# Test 7: Validation on ended session
# -------------------------------------------------

print("14. Testing ended session validation...")

try:
    service.process_verification(
        session_id=session_id,
        verification=successful_verification,
        attendance_date="2026-09-08",
        attendance_time="10:10:00",
    )
    raise RuntimeError("Expected ValueError when session is ended.")
except ValueError:
    print("   PASS (correctly caught ValueError for ended session)")


# -------------------------------------------------
# Cleanup test data
# -------------------------------------------------

print("15. Cleaning temporary test data...")

with get_connection() as connection:
    connection.execute(
        """
        DELETE FROM attendance
        WHERE session_id = ?
        """,
        (session_id,),
    )
    connection.execute(
        """
        DELETE FROM attendance_sessions
        WHERE session_id = ?
        """,
        (session_id,),
    )
    connection.execute(
        """
        DELETE FROM exams
        WHERE exam_id = ?
        """,
        (exam_id,),
    )
    connection.execute(
        """
        DELETE FROM classes
        WHERE class_id = ?
        """,
        (class_id,),
    )
    connection.commit()

delete_student(TEST_STUDENT_ID)

print("   PASS")

print()
print("ALL ATTENDANCE PROCESSING SERVICE TESTS PASSED")
