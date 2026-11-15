import os
import sys
sys.path.insert(0, os.path.abspath("."))

import cv2

from backend.ai.liveness_detector import LivenessDetector
from backend.ai.eye_landmarks import EyeLandmarks
from backend.ai.eye_aspect_ratio import EyeAspectRatio


print("===== REAL EAR TEST =====")


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

print(f"   Landmarks detected: {len(landmarks)}")
print("   PASS")


print("4. Extracting eye landmarks...")

eyes = EyeLandmarks.get_both_eyes(
    landmarks
)

left_eye = eyes["left_eye"]
right_eye = eyes["right_eye"]

print("   PASS")


print("5. Calculating left eye EAR...")

left_ear = EyeAspectRatio.calculate(
    left_eye
)

print(f"   Left eye EAR: {left_ear:.6f}")
print("   PASS")


print("6. Calculating right eye EAR...")

right_ear = EyeAspectRatio.calculate(
    right_eye
)

print(f"   Right eye EAR: {right_ear:.6f}")
print("   PASS")


print("7. Calculating average EAR...")

average_ear = (
    left_ear + right_ear
) / 2.0

print(f"   Average EAR: {average_ear:.6f}")
print("   PASS")


print("8. Releasing MediaPipe resources...")

detector.close()

print("   PASS")


print("ALL REAL EAR TESTS PASSED")