from types import SimpleNamespace

import cv2
import numpy as np

from backend.services.verification_service import VerificationService


print("===== VERIFICATION SERVICE TEST =====")


# -------------------------------------------------
# Fake Face
# -------------------------------------------------

class FakeFace:
    """
    Simple fake face object containing an embedding.
    """

    def __init__(self, embedding):
        self.embedding = embedding


# -------------------------------------------------
# Fake Face Engine
# -------------------------------------------------

class FakeFaceEngine:
    """
    Fake face engine used to isolate the
    VerificationService logic.
    """

    def __init__(self, faces=None):
        self.faces = faces or []

    def detect_faces(self, frame):
        return self.faces

    def get_embedding(self, face):
        return face.embedding


# -------------------------------------------------
# Fake Face Matcher
# -------------------------------------------------

class FakeFaceMatcher:
    """
    Fake matcher with controllable match result.
    """

    def __init__(
        self,
        matched=True,
        student_id="STUDENT001",
        similarity=0.85,
    ):
        self.matched = matched
        self.student_id = student_id
        self.similarity = similarity

    def find_best_match(self, embedding):

        if not self.matched:

            return {
                "student_id": None,
                "similarity": self.similarity,
                "matched": False,
            }

        return {
            "student_id": self.student_id,
            "similarity": self.similarity,
            "matched": True,
        }


# -------------------------------------------------
# Fake Liveness Service
# -------------------------------------------------

class FakeLivenessService:
    """
    Fake liveness service with controllable result.
    """

    def __init__(self, verified=False):
        self.verified = verified
        self.reset_called = False
        self.close_called = False

    def process_frame(self, frame):

        return {
            "face_detected": True,
            "liveness_verified": self.verified,
            "blink_detected": self.verified,
            "blink_count": 1 if self.verified else 0,
            "left_ear": 0.30,
            "right_ear": 0.30,
            "average_ear": 0.30,
        }

    def reset(self):
        self.reset_called = True

    def close(self):
        self.close_called = True


# -------------------------------------------------
# Test image
# -------------------------------------------------

print("1. Loading test image...")

image = cv2.imread(
    "tests/test_face.jpg"
)

if image is None:
    raise FileNotFoundError(
        "tests/test_face.jpg not found."
    )

print("   PASS")


# -------------------------------------------------
# Test embedding
# -------------------------------------------------

print("2. Creating test face embedding...")

embedding = np.ones(
    512,
    dtype=np.float32
)

fake_face = FakeFace(
    embedding
)

print("   Embedding shape:", embedding.shape)
print("   PASS")


# -------------------------------------------------
# Test 1: No face
# -------------------------------------------------

print("3. Testing no face detected...")

face_engine = FakeFaceEngine(
    faces=[]
)

matcher = FakeFaceMatcher()

liveness = FakeLivenessService(
    verified=True
)

service = VerificationService(
    face_engine=face_engine,
    face_matcher=matcher,
    liveness_service=liveness,
)

result = service.verify_frame(
    image
)

print(
    "   Reason:",
    result["reason"]
)

if result["verified"]:
    raise RuntimeError(
        "Verification must fail when no face is detected."
    )

if result["face_detected"]:
    raise RuntimeError(
        "face_detected should be False."
    )

print("   PASS")


# -------------------------------------------------
# Test 2: Multiple faces
# -------------------------------------------------

print("4. Testing multiple faces...")

face_engine.faces = [
    fake_face,
    fake_face,
]

result = service.verify_frame(
    image
)

print(
    "   Reason:",
    result["reason"]
)

if result["verified"]:
    raise RuntimeError(
        "Verification must fail with multiple faces."
    )

if not result["face_detected"]:
    raise RuntimeError(
        "face_detected should be True."
    )

if result["face_matched"]:
    raise RuntimeError(
        "Face should not be matched with multiple faces."
    )

print("   PASS")


# -------------------------------------------------
# Test 3: Unknown face
# -------------------------------------------------

print("5. Testing unknown face...")

face_engine.faces = [
    fake_face,
]

matcher.matched = False

result = service.verify_frame(
    image
)

print(
    "   Similarity:",
    result["similarity"]
)

print(
    "   Reason:",
    result["reason"]
)

if result["verified"]:
    raise RuntimeError(
        "Unknown face must not be verified."
    )

if result["face_matched"]:
    raise RuntimeError(
        "Unknown face should not be marked as matched."
    )

print("   PASS")


# -------------------------------------------------
# Test 4: Recognized face but liveness fails
# -------------------------------------------------

print("6. Testing recognized face with failed liveness...")

matcher.matched = True
matcher.student_id = "STUDENT001"
matcher.similarity = 0.85

liveness.verified = False

result = service.verify_frame(
    image
)

print(
    "   Student ID:",
    result["student_id"]
)

print(
    "   Similarity:",
    result["similarity"]
)

print(
    "   Liveness verified:",
    result["liveness_verified"]
)

print(
    "   Reason:",
    result["reason"]
)

if result["verified"]:
    raise RuntimeError(
        "Verification must fail when liveness fails."
    )

if not result["face_matched"]:
    raise RuntimeError(
        "Face should be recognized."
    )

if result["liveness_verified"]:
    raise RuntimeError(
        "Liveness should be False."
    )

if result["student_id"] != "STUDENT001":
    raise RuntimeError(
        "Incorrect student ID."
    )

print("   PASS")


# -------------------------------------------------
# Test 5: Face + liveness successful
# -------------------------------------------------

print("7. Testing successful verification...")

liveness.verified = True

result = service.verify_frame(
    image
)

print(
    "   Student ID:",
    result["student_id"]
)

print(
    "   Similarity:",
    result["similarity"]
)

print(
    "   Face matched:",
    result["face_matched"]
)

print(
    "   Liveness verified:",
    result["liveness_verified"]
)

print(
    "   Verified:",
    result["verified"]
)

print(
    "   Reason:",
    result["reason"]
)

if not result["verified"]:
    raise RuntimeError(
        "Student should be successfully verified."
    )

if result["student_id"] != "STUDENT001":
    raise RuntimeError(
        "Incorrect student ID."
    )

if result["similarity"] != 0.85:
    raise RuntimeError(
        "Incorrect similarity score."
    )

if not result["face_matched"]:
    raise RuntimeError(
        "Face should be matched."
    )

if not result["liveness_verified"]:
    raise RuntimeError(
        "Liveness should be verified."
    )

print("   PASS")


# -------------------------------------------------
# Test 6: Reset liveness
# -------------------------------------------------

print("8. Testing liveness reset...")

service.reset_liveness()

if not liveness.reset_called:
    raise RuntimeError(
        "Liveness reset was not called."
    )

print("   PASS")


# -------------------------------------------------
# Test 7: Close resources
# -------------------------------------------------

print("9. Testing resource cleanup...")

service.close()

if not liveness.close_called:
    raise RuntimeError(
        "Liveness service close was not called."
    )

print("   PASS")


# -------------------------------------------------
# Test 8: Invalid frame
# -------------------------------------------------

print("10. Testing invalid frame...")

try:

    service.verify_frame(None)

    raise RuntimeError(
        "None frame should raise ValueError."
    )

except ValueError as error:

    print(
        "   Error:",
        error
    )

print("   PASS")


print()
print("ALL VERIFICATION SERVICE TESTS PASSED")