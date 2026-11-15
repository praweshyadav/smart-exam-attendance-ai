import cv2

from backend.ai.liveness_detector import LivenessDetector


print("===== LIVENESS DETECTOR TEST =====")

print("1. Loading test image...")
image = cv2.imread("tests/test_face.jpg")

if image is None:
    raise FileNotFoundError(
        "tests/test_face.jpg not found."
    )

print("   PASS")

print("2. Creating LivenessDetector...")
detector = LivenessDetector()

print("   PASS")

print("3. Detecting face...")
face_detected = detector.detect_face(image)

print(f"   Face detected: {face_detected}")

if not face_detected:
    detector.close()
    raise RuntimeError(
        "No face detected in test image."
    )

print("   PASS")

print("4. Getting face landmarks...")
landmarks = detector.get_landmarks(image)

if landmarks is None:
    detector.close()
    raise RuntimeError(
        "Face landmarks were not detected."
    )

print(f"   Number of landmarks: {len(landmarks)}")

if len(landmarks) < 468:
    detector.close()
    raise RuntimeError(
        "Unexpected number of face landmarks."
    )

print("   PASS")

print("5. Releasing MediaPipe resources...")
detector.close()

print("   PASS")

print("ALL LIVENESS DETECTOR TESTS PASSED")