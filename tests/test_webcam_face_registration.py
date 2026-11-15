import time

import cv2

from backend.database.database import get_connection
from backend.ai.face_database import FaceDatabase
from backend.services.face_registration_service import (
    FaceRegistrationService,
)
from backend.services.student_service import (
    add_student,
    delete_student,
)


print("===== WEBCAM FACE REGISTRATION TEST =====")


# -------------------------------------------------
# Configuration
# -------------------------------------------------

TEST_STUDENT_ID = "TEST_WEBCAM_001"
TEST_STUDENT_NAME = "Webcam Test Student"

CAMERA_INDEX = 0
CAPTURE_DELAY = 3


# -------------------------------------------------
# Clean previous test student
# -------------------------------------------------

print("1. Cleaning previous test data...")

# Remove any leftover face embedding from
# a previous interrupted test.
face_database = FaceDatabase()

face_database.delete_embedding(
    TEST_STUDENT_ID
)

# Remove any leftover student record.
delete_student(
    TEST_STUDENT_ID
)

print("   PASS")


# -------------------------------------------------
# Create test student
# -------------------------------------------------

print("2. Creating temporary test student...")

created = add_student(
    TEST_STUDENT_ID,
    TEST_STUDENT_NAME,
)

if not created:
    raise RuntimeError(
        "Temporary test student could not be created."
    )

print("   PASS")


# -------------------------------------------------
# Create registration service
# -------------------------------------------------

print("3. Creating FaceRegistrationService...")

registration_service = FaceRegistrationService()

print("   PASS")


# -------------------------------------------------
# Open webcam
# -------------------------------------------------

print("4. Opening webcam...")

camera = cv2.VideoCapture(
    CAMERA_INDEX
)

if not camera.isOpened():
    delete_student(TEST_STUDENT_ID)

    raise RuntimeError(
        "Could not open webcam."
    )

print("   PASS")


# -------------------------------------------------
# Countdown
# -------------------------------------------------

print()
print("Get ready.")
print("Look directly at the camera.")
print("Make sure exactly ONE face is visible.")
print()

for countdown in [3, 2, 1]:

    success, frame = camera.read()

    if not success:

        camera.release()

        cv2.destroyAllWindows()

        delete_student(TEST_STUDENT_ID)

        raise RuntimeError(
            "Could not read webcam frame."
        )

    display_frame = frame.copy()

    cv2.putText(
        display_frame,
        "FACE REGISTRATION TEST",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
    )

    cv2.putText(
        display_frame,
        f"Starting in {countdown}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
    )

    cv2.imshow(
        "Webcam Face Registration Test",
        display_frame,
    )

    key = cv2.waitKey(1000) & 0xFF

    if key == ord("q"):

        camera.release()

        cv2.destroyAllWindows()

        delete_student(TEST_STUDENT_ID)

        print("Test cancelled.")

        raise SystemExit


# -------------------------------------------------
# Capture frame
# -------------------------------------------------

print("5. Capturing webcam frame...")

success, frame = camera.read()

camera.release()

cv2.destroyAllWindows()

if not success:

    delete_student(TEST_STUDENT_ID)

    raise RuntimeError(
        "Could not capture webcam frame."
    )

print("   PASS")


# -------------------------------------------------
# Register face
# -------------------------------------------------

print("6. Registering face...")

result = registration_service.register_face(
    TEST_STUDENT_ID,
    frame,
)

print(
    f"   Success: {result['success']}"
)

print(
    f"   Reason: {result['reason']}"
)

if not result["success"]:

    delete_student(TEST_STUDENT_ID)

    raise RuntimeError(
        "Face registration failed: "
        + result["reason"]
    )

print(
    f"   Student ID: "
    f"{result['student_id']}"
)

print(
    f"   Embedding shape: "
    f"{result['embedding_shape']}"
)

if result["student_id"] != TEST_STUDENT_ID:

    delete_student(TEST_STUDENT_ID)

    raise RuntimeError(
        "Incorrect student ID."
    )

if result["embedding_shape"] != (512,):

    delete_student(TEST_STUDENT_ID)

    raise RuntimeError(
        "Incorrect embedding shape."
    )

print("   PASS")


# -------------------------------------------------
# Verify database status
# -------------------------------------------------

print("7. Checking database face registration status...")

with get_connection() as connection:

    student = connection.execute(
        """
        SELECT
            student_id,
            student_name,
            face_registered
        FROM students
        WHERE student_id = ?
        """,
        (TEST_STUDENT_ID,),
    ).fetchone()

if student is None:

    delete_student(TEST_STUDENT_ID)

    raise RuntimeError(
        "Test student was not found."
    )

print(
    f"   Student ID: "
    f"{student['student_id']}"
)

print(
    f"   Face registered: "
    f"{student['face_registered']}"
)

if student["face_registered"] != 1:

    delete_student(TEST_STUDENT_ID)

    raise RuntimeError(
        "Face registration status was not updated."
    )

print("   PASS")


# -------------------------------------------------
# Verify face database
# -------------------------------------------------

print("8. Checking face database...")

from backend.ai.face_database import FaceDatabase

face_database = FaceDatabase()

if not face_database.embedding_exists(
    TEST_STUDENT_ID
):

    delete_student(TEST_STUDENT_ID)

    raise RuntimeError(
        "Face embedding was not saved."
    )

embedding = face_database.get_embedding(
    TEST_STUDENT_ID
)

print(
    f"   Embedding shape: "
    f"{embedding.shape}"
)

if embedding.shape != (512,):

    delete_student(TEST_STUDENT_ID)

    raise RuntimeError(
        "Stored embedding has incorrect shape."
    )

print("   PASS")


# -------------------------------------------------
# Cleanup
# -------------------------------------------------

print("9. Cleaning temporary test data...")

from backend.ai.face_database import FaceDatabase

face_database = FaceDatabase()

deleted_embedding = face_database.delete_embedding(
    TEST_STUDENT_ID
)

if not deleted_embedding:

    raise RuntimeError(
        "Temporary face embedding could not be deleted."
    )

deleted_student = delete_student(
    TEST_STUDENT_ID
)

if not deleted_student:

    raise RuntimeError(
        "Temporary test student could not be deleted."
    )

print("   PASS")


# -------------------------------------------------
# Verify cleanup
# -------------------------------------------------

print("10. Verifying cleanup...")

with get_connection() as connection:

    remaining_student = connection.execute(
        """
        SELECT student_id
        FROM students
        WHERE student_id = ?
        """,
        (TEST_STUDENT_ID,),
    ).fetchone()

if remaining_student is not None:

    raise RuntimeError(
        "Temporary student still exists."
    )

face_database = FaceDatabase()

if face_database.embedding_exists(
    TEST_STUDENT_ID
):

    raise RuntimeError(
        "Temporary face embedding still exists."
    )

print("   PASS")


print()
print("ALL WEBCAM FACE REGISTRATION TESTS PASSED")