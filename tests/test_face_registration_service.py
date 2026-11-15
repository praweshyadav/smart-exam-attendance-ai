import cv2

from backend.ai.face_database import FaceDatabase
from backend.ai.face_engine import FaceEngine
from backend.services.face_registration_service import (
    FaceRegistrationService,
)
from backend.services.student_service import (
    add_student,
    delete_student,
    get_student,
)


print("===== FACE REGISTRATION SERVICE TEST =====")


TEST_STUDENT_ID = "TEST_FACE_REG_001"


# Clean up previous test data if it exists.
delete_student(TEST_STUDENT_ID)


print("1. Creating test student...")

created = add_student(
    TEST_STUDENT_ID,
    "Test Face Registration Student"
)

if not created:
    raise RuntimeError("Test student was not created.")

print("   PASS")


print("2. Loading test image...")

image = cv2.imread("tests/test_face.jpg")

if image is None:
    raise FileNotFoundError(
        "tests/test_face.jpg could not be loaded."
    )

print("   PASS")


print("3. Creating isolated face database...")

face_database = FaceDatabase()

# Keep the test isolated from the real face database.
face_database._database = {}

print("   PASS")


print("4. Creating Face Registration Service...")

face_engine = FaceEngine()

service = FaceRegistrationService(
    face_engine=face_engine,
    face_database=face_database,
)

print("   PASS")


print("5. Registering face...")

result = service.register_face(
    TEST_STUDENT_ID,
    image
)

print(f"   Result: {result}")

if not result["success"]:
    raise RuntimeError(
        f"Face registration failed: {result['reason']}"
    )

print("   PASS")


print("6. Checking face embedding...")

if not face_database.embedding_exists(
    TEST_STUDENT_ID
):
    raise RuntimeError(
        "Face embedding was not saved."
    )

embedding = face_database.get_embedding(
    TEST_STUDENT_ID
)

if embedding.shape != (512,):
    raise RuntimeError(
        "Stored embedding has incorrect shape."
    )

print(f"   Embedding shape: {embedding.shape}")
print("   PASS")


print("7. Checking student registration status...")

student = get_student(TEST_STUDENT_ID)

if student is None:
    raise RuntimeError(
        "Test student could not be retrieved."
    )

if student["face_registered"] != 1:
    raise RuntimeError(
        "Student face_registered was not updated."
    )

print("   PASS")


print("8. Testing duplicate registration protection...")

duplicate_result = service.register_face(
    TEST_STUDENT_ID,
    image
)

print(f"   Result: {duplicate_result}")

if duplicate_result["success"]:
    raise RuntimeError(
        "Duplicate face registration should be rejected."
    )

print("   PASS")


print("9. Cleaning up test student...")

deleted = delete_student(TEST_STUDENT_ID)

if not deleted:
    raise RuntimeError(
        "Test student could not be deleted."
    )

print("   PASS")


print("ALL FACE REGISTRATION SERVICE TESTS PASSED")