import cv2

from backend.ai.face_database import FaceDatabase
from backend.ai.face_engine import FaceEngine
from backend.ai.face_matcher import FaceMatcher
from backend.database.database import get_connection
from backend.services.face_registration_service import (
    FaceRegistrationService,
)
from backend.services.student_service import (
    add_student,
    delete_student,
)


print("===== WEBCAM FACE VERIFICATION TEST =====")


# -------------------------------------------------
# Configuration
# -------------------------------------------------

TEST_STUDENT_ID = "TEST_VERIFY_001"
TEST_STUDENT_NAME = "Webcam Verification Student"

CAMERA_INDEX = 0


# -------------------------------------------------
# Clean previous test data
# -------------------------------------------------

print("1. Cleaning previous test data...")

face_database = FaceDatabase()

face_database.delete_embedding(
    TEST_STUDENT_ID
)

delete_student(
    TEST_STUDENT_ID
)

print("   PASS")


# -------------------------------------------------
# Create temporary student
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
# Create face components
# -------------------------------------------------

print("3. Creating face recognition components...")

face_engine = FaceEngine()

face_database = FaceDatabase()

face_matcher = FaceMatcher(
    database=face_database
)

registration_service = FaceRegistrationService(
    face_engine=face_engine,
    face_database=face_database,
)

print("   PASS")


# -------------------------------------------------
# Open webcam
# -------------------------------------------------

print("4. Opening webcam...")

camera = cv2.VideoCapture(
    CAMERA_INDEX
)

if not camera.isOpened():

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "Could not open webcam."
    )

print("   PASS")


# -------------------------------------------------
# Registration countdown
# -------------------------------------------------

print()
print("==============================================")
print("FACE REGISTRATION")
print("==============================================")
print("Look directly at the camera.")
print("Make sure exactly ONE face is visible.")
print()

for countdown in [3, 2, 1]:

    success, frame = camera.read()

    if not success:

        camera.release()
        cv2.destroyAllWindows()

        delete_student(
            TEST_STUDENT_ID
        )

        face_database.delete_embedding(
            TEST_STUDENT_ID
        )

        raise RuntimeError(
            "Could not read webcam frame."
        )

    display_frame = frame.copy()

    cv2.putText(
        display_frame,
        "FACE REGISTRATION",
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
        "Webcam Face Verification Test",
        display_frame,
    )

    key = cv2.waitKey(1000) & 0xFF

    if key == ord("q"):

        camera.release()
        cv2.destroyAllWindows()

        delete_student(
            TEST_STUDENT_ID
        )

        face_database.delete_embedding(
            TEST_STUDENT_ID
        )

        print("Test cancelled.")

        raise SystemExit


# -------------------------------------------------
# Capture registration frame
# -------------------------------------------------

print("5. Capturing registration frame...")

success, registration_frame = camera.read()

if not success:

    camera.release()
    cv2.destroyAllWindows()

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "Could not capture registration frame."
    )

print("   PASS")


# -------------------------------------------------
# Register face
# -------------------------------------------------

print("6. Registering face...")

registration_result = (
    registration_service.register_face(
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

if not registration_result["success"]:

    camera.release()
    cv2.destroyAllWindows()

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "Face registration failed: "
        + registration_result["reason"]
    )

print(
    f"   Embedding shape: "
    f"{registration_result['embedding_shape']}"
)

if registration_result["embedding_shape"] != (512,):

    camera.release()
    cv2.destroyAllWindows()

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "Registration embedding has incorrect shape."
    )

print("   PASS")


# -------------------------------------------------
# Verification countdown
# -------------------------------------------------

print()
print("==============================================")
print("FACE VERIFICATION")
print("==============================================")
print("Move slightly or change your expression.")
print("This should be a NEW webcam frame.")
print()

for countdown in [3, 2, 1]:

    success, frame = camera.read()

    if not success:

        camera.release()
        cv2.destroyAllWindows()

        delete_student(
            TEST_STUDENT_ID
        )

        face_database.delete_embedding(
            TEST_STUDENT_ID
        )

        raise RuntimeError(
            "Could not read webcam frame."
        )

    display_frame = frame.copy()

    cv2.putText(
        display_frame,
        "FACE VERIFICATION",
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
        "Webcam Face Verification Test",
        display_frame,
    )

    key = cv2.waitKey(1000) & 0xFF

    if key == ord("q"):

        camera.release()
        cv2.destroyAllWindows()

        delete_student(
            TEST_STUDENT_ID
        )

        face_database.delete_embedding(
            TEST_STUDENT_ID
        )

        print("Test cancelled.")

        raise SystemExit


# -------------------------------------------------
# Capture verification frame
# -------------------------------------------------

print("7. Capturing NEW verification frame...")

success, verification_frame = camera.read()

camera.release()

cv2.destroyAllWindows()

if not success:

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "Could not capture verification frame."
    )

print("   PASS")


# -------------------------------------------------
# Detect face
# -------------------------------------------------

print("8. Detecting face in verification frame...")

faces = face_engine.detect_faces(
    verification_frame
)

print(
    f"   Faces detected: "
    f"{len(faces)}"
)

if len(faces) == 0:

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "No face detected in verification frame."
    )

if len(faces) > 1:

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "Multiple faces detected in verification frame."
    )

print("   PASS")


# -------------------------------------------------
# Generate verification embedding
# -------------------------------------------------

print("9. Generating verification embedding...")

verification_embedding = (
    face_engine.get_embedding(
        faces[0]
    )
)

print(
    f"   Embedding shape: "
    f"{verification_embedding.shape}"
)

if verification_embedding.shape != (512,):

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "Verification embedding has incorrect shape."
    )

print("   PASS")


# -------------------------------------------------
# Face matching
# -------------------------------------------------

print("10. Matching verification face...")

match_result = (
    face_matcher.find_best_match(
        verification_embedding
    )
)

print(
    f"   Matched: "
    f"{match_result['matched']}"
)

print(
    f"   Student ID: "
    f"{match_result['student_id']}"
)

print(
    f"   Similarity: "
    f"{match_result['similarity']}"
)

if not match_result["matched"]:

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "Registered face was not recognized."
    )

if match_result["student_id"] != TEST_STUDENT_ID:

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "Incorrect student was recognized."
    )

if match_result["similarity"] < 0.45:

    delete_student(
        TEST_STUDENT_ID
    )

    face_database.delete_embedding(
        TEST_STUDENT_ID
    )

    raise RuntimeError(
        "Similarity is below the configured threshold."
    )

print("   PASS")


# -------------------------------------------------
# Cleanup
# -------------------------------------------------

print("11. Cleaning temporary test data...")

deleted_embedding = (
    face_database.delete_embedding(
        TEST_STUDENT_ID
    )
)

if not deleted_embedding:

    delete_student(
        TEST_STUDENT_ID
    )

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

print("12. Verifying cleanup...")

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
print("ALL WEBCAM FACE VERIFICATION TESTS PASSED")