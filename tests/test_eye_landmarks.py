import cv2

from backend.ai.liveness_detector import LivenessDetector
from backend.ai.eye_landmarks import EyeLandmarks


print("===== EYE LANDMARKS TEST =====")


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


print("3. Getting face landmarks...")

landmarks = detector.get_landmarks(image)

if landmarks is None:
    detector.close()

    raise RuntimeError(
        "No face landmarks detected."
    )

print(f"   Number of landmarks: {len(landmarks)}")

if len(landmarks) != 478:
    detector.close()

    raise RuntimeError(
        "Expected 478 face landmarks."
    )

print("   PASS")


print("4. Extracting left eye landmarks...")

left_eye = EyeLandmarks.get_left_eye(
    landmarks
)

print(f"   Left eye points: {len(left_eye)}")

if len(left_eye) != 6:
    detector.close()

    raise RuntimeError(
        "Left eye should contain exactly 6 points."
    )

print("   PASS")


print("5. Extracting right eye landmarks...")

right_eye = EyeLandmarks.get_right_eye(
    landmarks
)

print(f"   Right eye points: {len(right_eye)}")

if len(right_eye) != 6:
    detector.close()

    raise RuntimeError(
        "Right eye should contain exactly 6 points."
    )

print("   PASS")


print("6. Checking landmark point format...")

for point in left_eye + right_eye:

    if len(point) != 2:
        detector.close()

        raise RuntimeError(
            "Each eye point must contain x and y coordinates."
        )

    if not all(
        isinstance(value, float)
        for value in point
    ):
        detector.close()

        raise RuntimeError(
            "Eye coordinates must be floating-point values."
        )

print("   PASS")


print("7. Testing both-eye extraction...")

both_eyes = EyeLandmarks.get_both_eyes(
    landmarks
)

if "left_eye" not in both_eyes:
    detector.close()

    raise RuntimeError(
        "Left eye missing from result."
    )

if "right_eye" not in both_eyes:
    detector.close()

    raise RuntimeError(
        "Right eye missing from result."
    )

print("   PASS")


print("8. Releasing MediaPipe resources...")

detector.close()

print("   PASS")


print("ALL EYE LANDMARKS TESTS PASSED")