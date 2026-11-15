import numpy as np

from backend.ai.face_validator import FaceValidator


class MockFace:
    def __init__(self, embedding):
        self.embedding = embedding


print("===== FACE VALIDATOR TEST =====")


print("1. Testing no face...")

result = FaceValidator.validate([])

print(f"   Result: {result}")

if result["valid"]:
    raise RuntimeError("Empty face list should be invalid.")

print("   PASS")


print("2. Testing multiple faces...")

face_a = MockFace(np.random.rand(512).astype(np.float32))
face_b = MockFace(np.random.rand(512).astype(np.float32))

result = FaceValidator.validate([
    face_a,
    face_b
])

print(f"   Result: {result}")

if result["valid"]:
    raise RuntimeError(
        "Multiple faces should be invalid."
    )

print("   PASS")


print("3. Testing invalid embedding shape...")

invalid_face = MockFace(
    np.random.rand(128).astype(np.float32)
)

result = FaceValidator.validate([
    invalid_face
])

print(f"   Result: {result}")

if result["valid"]:
    raise RuntimeError(
        "Invalid embedding shape should be rejected."
    )

print("   PASS")


print("4. Testing missing embedding...")

missing_embedding_face = MockFace(None)

result = FaceValidator.validate([
    missing_embedding_face
])

print(f"   Result: {result}")

if result["valid"]:
    raise RuntimeError(
        "Missing embedding should be rejected."
    )

print("   PASS")


print("5. Testing exactly one valid face...")

valid_embedding = np.random.rand(
    512
).astype(np.float32)

valid_face = MockFace(valid_embedding)

result = FaceValidator.validate([
    valid_face
])

print(f"   Result: {result}")

if not result["valid"]:
    raise RuntimeError(
        "Exactly one valid face should be accepted."
    )

print("   PASS")


print("ALL FACE VALIDATOR TESTS PASSED")