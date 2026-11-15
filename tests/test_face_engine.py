import cv2

from backend.ai.face_engine import FaceEngine


print("===== FACE ENGINE TEST =====")

print("1. Loading FaceEngine...")
engine = FaceEngine()
print("   PASS")

print("2. Loading test image...")

image = cv2.imread("tests/test_face.jpg")

if image is None:
    raise FileNotFoundError(
        "tests/test_face.jpg not found."
    )

print("   PASS")

print("3. Detecting faces...")

faces = engine.detect_faces(image)

print(f"   Faces detected: {len(faces)}")

if len(faces) == 0:
    raise RuntimeError("No face detected in test image.")

print("   PASS")

print("4. Checking embedding...")

embedding = engine.get_embedding(faces[0])

print(f"   Embedding shape: {embedding.shape}")

if embedding is None:
    raise RuntimeError("Face embedding was not generated.")

print("   PASS")

print("ALL FACE ENGINE TESTS PASSED")