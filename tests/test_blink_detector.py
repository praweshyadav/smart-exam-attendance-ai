from types import SimpleNamespace

from backend.ai.blink_detector import BlinkDetector
from backend.ai.eye_landmarks import EyeLandmarks


print("===== BLINK DETECTOR TEST =====")


def create_landmarks(eye_points):
    """
    Create fake MediaPipe-style landmarks.

    The fake landmarks contain x and y attributes,
    just like real MediaPipe landmarks.
    """

    landmarks = [
        SimpleNamespace(x=0.0, y=0.0)
        for _ in range(478)
    ]

    for index, point in zip(
        EyeLandmarks.LEFT_EYE_INDICES,
        eye_points,
    ):
        landmarks[index] = SimpleNamespace(
            x=point[0],
            y=point[1],
        )

    for index, point in zip(
        EyeLandmarks.RIGHT_EYE_INDICES,
        eye_points,
    ):
        landmarks[index] = SimpleNamespace(
            x=point[0],
            y=point[1],
        )

    return landmarks


print("1. Creating BlinkDetector...")

detector = BlinkDetector(
    blink_threshold=0.15,
    min_closed_frames=2,
)

print("   PASS")


print("2. Creating open-eye landmarks...")

open_eye = [
    [0.0, 0.0],
    [1.0, 1.0],
    [3.0, 1.0],
    [4.0, 0.0],
    [3.0, -1.0],
    [1.0, -1.0],
]

open_landmarks = create_landmarks(
    open_eye
)

print("   PASS")


print("3. Testing EAR calculation...")

ear_result = detector.calculate_ear(
    open_landmarks
)

print(
    f"   Average EAR: "
    f"{ear_result['average_ear']:.4f}"
)

if ear_result["average_ear"] <= 0:
    raise RuntimeError(
        "EAR should be greater than zero."
    )

print("   PASS")


print("4. Testing open-eye frame...")

result = detector.process_landmarks(
    open_landmarks
)

print(
    f"   EAR: {result['average_ear']:.4f}"
)

print(
    f"   Blink detected: "
    f"{result['blink_detected']}"
)

if result["blink_detected"]:
    raise RuntimeError(
        "Blink should not be detected with open eyes."
    )

print("   PASS")


print("5. Creating closed-eye landmarks...")

closed_eye = [
    [0.0, 0.0],
    [1.0, 0.05],
    [3.0, 0.05],
    [4.0, 0.0],
    [3.0, -0.05],
    [1.0, -0.05],
]

closed_landmarks = create_landmarks(
    closed_eye
)

print("   PASS")


print("6. Testing first closed-eye frame...")

result = detector.process_landmarks(
    closed_landmarks
)

print(
    f"   EAR: {result['average_ear']:.4f}"
)

print(
    f"   Blink detected: "
    f"{result['blink_detected']}"
)

if result["blink_detected"]:
    raise RuntimeError(
        "Blink should not be detected after "
        "only one closed frame."
    )

print("   PASS")


print("7. Testing second closed-eye frame...")

result = detector.process_landmarks(
    closed_landmarks
)

print(
    f"   EAR: {result['average_ear']:.4f}"
)

print(
    f"   Blink detected: "
    f"{result['blink_detected']}"
)

if result["blink_detected"]:
    raise RuntimeError(
        "Blink should not be detected while "
        "the eyes remain closed."
    )

print("   PASS")


print("8. Testing eye reopening...")

result = detector.process_landmarks(
    open_landmarks
)

print(
    f"   EAR: {result['average_ear']:.4f}"
)

print(
    f"   Blink detected: "
    f"{result['blink_detected']}"
)

if not result["blink_detected"]:
    raise RuntimeError(
        "Blink should be detected when "
        "eyes reopen."
    )

if result["blink_count"] != 1:
    raise RuntimeError(
        "Blink count should be exactly 1."
    )

print("   PASS")


print("9. Testing detector reset...")

detector.reset()

if detector.closed_frames != 0:
    raise RuntimeError(
        "Closed frame counter was not reset."
    )

if detector.blink_count != 0:
    raise RuntimeError(
        "Blink count was not reset."
    )

print("   PASS")


print("10. Testing invalid threshold...")

try:
    BlinkDetector(
        blink_threshold=0,
        min_closed_frames=2,
    )
except ValueError:
    print("   PASS")
else:
    raise RuntimeError(
        "Invalid blink threshold was not rejected."
    )


print("11. Testing invalid frame count...")

try:
    BlinkDetector(
        blink_threshold=0.15,
        min_closed_frames=0,
    )
except ValueError:
    print("   PASS")
else:
    raise RuntimeError(
        "Invalid minimum closed frames "
        "was not rejected."
    )


print("ALL BLINK DETECTOR TESTS PASSED")