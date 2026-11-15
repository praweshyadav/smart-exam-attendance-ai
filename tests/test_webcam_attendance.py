import time
from datetime import datetime

import cv2

from backend.ai.face_database import FaceDatabase
from backend.ai.face_engine import FaceEngine
from backend.ai.face_matcher import FaceMatcher
from backend.ai.liveness_detector import LivenessDetector
from backend.ai.blink_detector import BlinkDetector
from backend.services.liveness_service import LivenessService
from backend.services.verification_service import VerificationService
from backend.services.verification_attempt_service import (
    VerificationAttemptService,
)
from backend.services.attendance_processing_service import (
    AttendanceProcessingService,
)
from backend.services.face_registration_service import (
    FaceRegistrationService,
)
from backend.services.student_service import (
    add_student,
    delete_student,
    get_student,
)
from backend.services.class_service import (
    add_class,
    delete_class,
)
from backend.services.exam_service import (
    add_exam,
    delete_exam,
)
from backend.services.attendance_session_service import (
    start_session,
    end_session,
    get_session,
)
from backend.services.attendance_service import (
    get_attendance_by_session,
)


TEST_STUDENT_ID = "TEST_WEBCAM_ATTENDANCE_001"
TEST_STUDENT_NAME = "Webcam Attendance Test Student"
TEST_CLASS_NAME = "Webcam Attendance Test Class"


def cleanup_previous_data(face_database):
    """
    Remove leftover test data from previous interrupted runs.
    """

    # Remove old face embedding
    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    # Remove old student
    delete_student(
        TEST_STUDENT_ID
    )

    # Remove old test class.
    # Student deletion above also removes the
    # student's database relationship.
    from backend.services.class_service import (
        get_all_classes,
    )

    existing_classes = [
        item
        for item in get_all_classes()
        if item["class_name"] == TEST_CLASS_NAME
    ]

    for class_data in existing_classes:
        delete_class(
            class_data["class_id"]
        )


def main():

    print(
        "===== REAL WEBCAM ATTENDANCE "
        "INTEGRATION TEST ====="
    )

    # -------------------------------------------------
    # STEP 1: Create AI components
    # -------------------------------------------------

    print(
        "1. Creating AI components..."
    )

    face_engine = FaceEngine()

    face_database = FaceDatabase()

    face_matcher = FaceMatcher(
        database=face_database
    )

    face_registration_service = (
        FaceRegistrationService(
            face_engine=face_engine,
            face_database=face_database,
        )
    )

    liveness_detector = (
        LivenessDetector()
    )

    blink_detector = (
        BlinkDetector()
    )

    liveness_service = (
        LivenessService(
            liveness_detector=liveness_detector,
            blink_detector=blink_detector,
        )
    )

    verification_service = (
        VerificationService(
            face_engine=face_engine,
            face_matcher=face_matcher,
            liveness_service=liveness_service,
        )
    )

    verification_attempt_service = (
        VerificationAttemptService()
    )

    attendance_processing_service = (
        AttendanceProcessingService(
            verification_attempt_service=(
                verification_attempt_service
            )
        )
    )

    print("   PASS")

    # -------------------------------------------------
    # STEP 2: Clean previous test data
    # -------------------------------------------------

    print(
        "2. Cleaning previous test data..."
    )

    cleanup_previous_data(
        face_database
    )

    print("   PASS")

    # -------------------------------------------------
    # STEP 3: Create test class
    # -------------------------------------------------

    print(
        "3. Creating temporary test class..."
    )

    class_created = add_class(
        TEST_CLASS_NAME,
        department="TEST",
        semester=1,
    )

    if not class_created:
        raise RuntimeError(
            "Could not create test class."
        )

    from backend.services.class_service import (
        get_all_classes,
    )

    test_classes = [
        item
        for item in get_all_classes()
        if item["class_name"] == TEST_CLASS_NAME
    ]

    if not test_classes:
        raise RuntimeError(
            "Test class could not be found."
        )

    test_class_id = test_classes[0][
        "class_id"
    ]

    print(
        f"   Class ID: {test_class_id}"
    )
    print("   PASS")

    # -------------------------------------------------
    # STEP 4: Create test student
    # -------------------------------------------------

    print(
        "4. Creating temporary test student..."
    )

    student_created = add_student(
        TEST_STUDENT_ID,
        TEST_STUDENT_NAME,
        test_class_id,
    )

    if not student_created:
        raise RuntimeError(
            "Could not create test student."
        )

    print("   PASS")

    # -------------------------------------------------
    # STEP 5: Create test exam
    # -------------------------------------------------

    print(
        "5. Creating temporary test exam..."
    )

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    exam_created = add_exam(
        exam_name="Webcam Attendance Test Exam",
        class_id=test_class_id,
        exam_date=today,
        start_time=datetime.now().strftime(
            "%H:%M"
        ),
    )

    if not exam_created:
        raise RuntimeError(
            "Could not create test exam."
        )

    from backend.services.exam_service import (
        get_all_exams,
    )

    test_exams = [
        item
        for item in get_all_exams()
        if item["exam_name"]
        == "Webcam Attendance Test Exam"
        and item["class_id"]
        == test_class_id
    ]

    if not test_exams:
        raise RuntimeError(
            "Test exam could not be found."
        )

    test_exam_id = test_exams[-1][
        "exam_id"
    ]

    print(
        f"   Exam ID: {test_exam_id}"
    )
    print("   PASS")

    # -------------------------------------------------
    # STEP 6: Start attendance session
    # -------------------------------------------------

    print(
        "6. Starting attendance session..."
    )

    session_id = start_session(
        test_exam_id
    )

    print(
        f"   Session ID: {session_id}"
    )
    print("   PASS")

    # -------------------------------------------------
    # STEP 7: Open webcam
    # -------------------------------------------------

    print(
        "7. Opening webcam..."
    )

    camera = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW
    )

    if not camera.isOpened():

        camera.release()

        camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        raise RuntimeError(
            "Could not open webcam."
        )

    print("   PASS")

    # -------------------------------------------------
    # STEP 8: Capture registration frame
    # -------------------------------------------------

    print()
    print(
        "=============================================="
    )
    print(
        "STEP 1: REGISTER YOUR FACE"
    )
    print(
        "=============================================="
    )

    print(
        "Look directly at the camera."
    )

    print(
        "Make sure exactly ONE face is visible."
    )

    print()

    input(
        "Press ENTER when ready..."
    )

    print()
    print(
        "8. Capturing registration frame..."
    )

    registration_frame = None

    for _ in range(30):

        success, frame = camera.read()

        if not success:
            continue

        registration_frame = frame

        cv2.imshow(
            "Registration",
            frame
        )

        if (
            cv2.waitKey(1)
            & 0xFF
            == ord("q")
        ):
            break

    cv2.destroyWindow(
        "Registration"
    )

    if registration_frame is None:

        raise RuntimeError(
            "Could not capture registration frame."
        )

    print("   PASS")

    # -------------------------------------------------
    # STEP 9: Register face
    # -------------------------------------------------

    print(
        "9. Registering face..."
    )

    registration_result = (
        face_registration_service.register_face(
            TEST_STUDENT_ID,
            registration_frame,
        )
    )

    print(
        f"   Success: "
        f"{registration_result['success']}"
    )

    print(
        f"   Reason: "
        f"{registration_result['reason']}"
    )

    if not registration_result[
        "success"
    ]:

        camera.release()

        raise RuntimeError(
            "Face registration failed."
        )

    print(
        "   Embedding shape: "
        f"{registration_result['embedding_shape']}"
    )

    print("   PASS")

    # -------------------------------------------------
    # STEP 10: Reset liveness
    # -------------------------------------------------

    verification_service.reset_liveness()

    print()
    print(
        "=============================================="
    )
    print(
        "STEP 2: FACE VERIFICATION + LIVENESS"
    )
    print(
        "=============================================="
    )

    print(
        "Keep looking at the camera."
    )

    print(
        "The system will recognize your face."
    )

    print(
        "Then BLINK naturally once."
    )

    print()

    print(
        "You have up to 20 seconds."
    )

    print()

    # -------------------------------------------------
    # STEP 11: Real-time verification
    # -------------------------------------------------

    print(
        "10. Checking real verification result..."
    )

    start_time = time.time()

    verification_result = None

    frame_count = 0

    while (
        time.time() - start_time
        < 20
    ):

        success, frame = camera.read()

        if not success:
            continue

        frame_count += 1

        verification_result = (
            verification_service.verify_frame(
                frame
            )
        )
        if frame_count % 10 == 0:
            print(
        f"Frame {frame_count}: "
        f"face={verification_result['face_detected']} | "
        f"matched={verification_result['face_matched']} | "
        f"similarity={verification_result['similarity']} | "
        f"liveness={verification_result['liveness_verified']} | "
        f"reason={verification_result['reason']}"
    )

        # ---------------------------------------------
        # Display status
        # ---------------------------------------------

        status_text = (
            "Face: "
            + (
                "Detected"
                if verification_result[
                    "face_detected"
                ]
                else "Not Detected"
            )
        )

        cv2.putText(
            frame,
            status_text,
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

        student_text = (
            "Student: "
            + str(
                verification_result[
                    "student_id"
                ]
            )
        )

        cv2.putText(
            frame,
            student_text,
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        similarity = (
            verification_result[
                "similarity"
            ]
        )

        similarity_text = (
            "Similarity: "
            + (
                f"{similarity:.3f}"
                if similarity is not None
                else "N/A"
            )
        )

        cv2.putText(
            frame,
            similarity_text,
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        liveness_text = (
            "Liveness: "
            + (
                "VERIFIED"
                if verification_result[
                    "liveness_verified"
                ]
                else "Waiting for blink"
            )
        )

        cv2.putText(
            frame,
            liveness_text,
            (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        cv2.imshow(
            "Attendance Verification",
            frame
        )

        # ---------------------------------------------
        # Successful verification
        # ---------------------------------------------

        if verification_result[
            "verified"
        ]:

            print()
            print(
                "   Face recognized successfully."
            )

            print(
                "   Student ID: "
                f"{verification_result['student_id']}"
            )

            print(
                "   Similarity: "
                f"{verification_result['similarity']}"
            )

            print(
                "   Liveness: VERIFIED"
            )

            print(
                "   PASS"
            )

            break

        key = (
            cv2.waitKey(1)
            & 0xFF
        )

        if key == ord("q"):

            verification_result = None

            break

    cv2.destroyWindow(
        "Attendance Verification"
    )

    # -------------------------------------------------
    # STEP 12: Validate verification
    # -------------------------------------------------

    if (
        verification_result is None
        or not verification_result[
            "verified"
        ]
    ):

        camera.release()

        raise RuntimeError(
            "Verification timed out or failed. "
            "Make sure your face is visible and "
            "blink naturally during the test."
        )

    # -------------------------------------------------
    # STEP 13: Process verified result
    # -------------------------------------------------

    print()
    print(
        "11. Processing verified result..."
    )

    attendance_date = datetime.now().strftime(
        "%Y-%m-%d"
    )

    attendance_time = datetime.now().strftime(
        "%H:%M:%S"
    )

    attendance_result = (
        attendance_processing_service.process_verification(
            session_id=session_id,
            verification=verification_result,
            attendance_date=attendance_date,
            attendance_time=attendance_time,
            student_name=TEST_STUDENT_NAME,
            status="Present",
        )
    )

    print(
        "   Attendance marked: "
        f"{attendance_result['attendance_marked']}"
    )

    print(
        "   Reason: "
        f"{attendance_result['reason']}"
    )

    if not attendance_result[
        "attendance_marked"
    ]:

        camera.release()

        raise RuntimeError(
            "Attendance was not marked."
        )

    print("   PASS")

    # -------------------------------------------------
    # STEP 14: Verify attendance in database
    # -------------------------------------------------

    print()
    print(
        "12. Checking attendance database..."
    )

    attendance_records = (
        get_attendance_by_session(
            session_id
        )
    )

    matching_records = [
        record
        for record in attendance_records
        if record["student_id"]
        == TEST_STUDENT_ID
    ]

    if len(matching_records) != 1:

        camera.release()

        raise RuntimeError(
            "Expected exactly one attendance "
            "record."
        )

    attendance_record = (
        matching_records[0]
    )

    print(
        "   Student ID: "
        f"{attendance_record['student_id']}"
    )

    print(
        "   Student Name: "
        f"{attendance_record['student_name']}"
    )

    print(
        "   Status: "
        f"{attendance_record['status']}"
    )

    print(
        "   Similarity: "
        f"{attendance_record['verification_score']}"
    )

    print("   PASS")

    # -------------------------------------------------
    # STEP 15: Test duplicate protection
    # -------------------------------------------------

    print()
    print(
        "13. Testing duplicate attendance protection..."
    )

    duplicate_result = (
        attendance_processing_service.process_verification(
            session_id=session_id,
            verification=verification_result,
            attendance_date=attendance_date,
            attendance_time=attendance_time,
            student_name=TEST_STUDENT_NAME,
            status="Present",
        )
    )

    if duplicate_result[
        "attendance_marked"
    ]:

        camera.release()

        raise RuntimeError(
            "Duplicate attendance was incorrectly marked."
        )

    print(
        "   Duplicate attendance prevented."
    )

    print("   PASS")

    # -------------------------------------------------
    # STEP 16: End session
    # -------------------------------------------------

    print()
    print(
        "14. Ending attendance session..."
    )

    session_ended = end_session(
        session_id
    )

    if not session_ended:

        camera.release()

        raise RuntimeError(
            "Could not end attendance session."
        )

    session = get_session(
        session_id
    )

    if session is None:
        camera.release()

        raise RuntimeError(
            "Attendance session not found."
        )

    if session["ended_at"] is None:

        camera.release()

        raise RuntimeError(
            "Attendance session was not ended."
        )

    print("   PASS")

    # -------------------------------------------------
    # STEP 17: Cleanup
    # -------------------------------------------------

    print()
    print(
        "15. Cleaning temporary test data..."
    )

    camera.release()

    cv2.destroyAllWindows()

    verification_service.close()

    # Delete face embedding first
    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    # Delete student
    delete_student(
        TEST_STUDENT_ID
    )

    # Delete exam
    delete_exam(
        test_exam_id
    )

    # Delete class
    delete_class(
        test_class_id
    )

    print("   PASS")

    # -------------------------------------------------
    # STEP 18: Verify cleanup
    # -------------------------------------------------

    print()
    print(
        "16. Verifying cleanup..."
    )

    remaining_student = get_student(
        TEST_STUDENT_ID
    )

    remaining_embedding = (
        face_database.get_embedding(
            TEST_STUDENT_ID
        )
    )

    if remaining_student is not None:

        raise RuntimeError(
            "Test student still exists."
        )

    if remaining_embedding is not None:

        raise RuntimeError(
            "Test face embedding still exists."
        )

    print("   PASS")

    print()
    print(
        "=============================================="
    )
    print(
        "ALL WEBCAM ATTENDANCE TESTS PASSED"
    )
    print(
        "=============================================="
    )


if __name__ == "__main__":
    main()