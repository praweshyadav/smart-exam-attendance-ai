from types import SimpleNamespace

import cv2

from backend.ai.blink_detector import BlinkDetector
from backend.ai.eye_landmarks import EyeLandmarks
from backend.ai.liveness_detector import LivenessDetector
from backend.services.liveness_service import LivenessService


print("===== LIVENESS SERVICE TEST =====")


def create_fake_landmarks(eye_points):
    """
    Create 478 MediaPipe-style landmarks
    with controlled eye coordinates.
    """

    landmarks = [
        SimpleNamespace(
            x=0.0,
            y=0.0,
        )
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


class FakeLivenessDetector:
    """
    Fake detector used to test LivenessService
    without depending on MediaPipe for every test.
    """

    def __init__(self, landmarks):
        self.landmarks = landmarks

    def process_frame(self, frame):
        """
        Return fake MediaPipe-style results.
        """

        return SimpleNamespace(
            face_landmarks=[
                self.landmarks
            ]
        )

    def close(self):
        """
        Fake resource cleanup.
        """

        pass


print("1. Loading test image...")

image = cv2.imread(
    "tests/test_face.jpg"
)

if image is None:
    raise FileNotFoundError(
        "tests/test_face.jpg not found."
    )

print("   PASS")


print("2. Creating fake open-eye landmarks...")

open_eye = [
    [0.0, 0.0],
    [1.0, 1.0],
    [3.0, 1.0],
    [4.0, 0.0],
    [3.0, -1.0],
    [1.0, -1.0],
]

open_landmarks = create_fake_landmarks(
    open_eye
)

print("   PASS")


print("3. Creating fake closed-eye landmarks...")

closed_eye = [
    [0.0, 0.0],
    [1.0, 0.05],
    [3.0, 0.05],
    [4.0, 0.0],
    [3.0, -0.05],
    [1.0, -0.05],
]

closed_landmarks = create_fake_landmarks(
    closed_eye
)

print("   PASS")


print("4. Creating LivenessService...")

fake_detector = FakeLivenessDetector(
    open_landmarks
)

blink_detector = BlinkDetector(
    blink_threshold=0.15,
    min_closed_frames=2,
)

service = LivenessService(
    liveness_detector=fake_detector,
    blink_detector=blink_detector,
)

print("   PASS")


print("5. Testing face detection...")

result = service.process_frame(
    image
)

print(
    f"   Face detected: "
    f"{result['face_detected']}"
)

if not result["face_detected"]:
    raise RuntimeError(
        "Face should be detected."
    )

print("   PASS")


print("6. Testing liveness before blink...")

if result["liveness_verified"]:
    raise RuntimeError(
        "Liveness should not be verified "
        "before a blink."
    )

print(
    f"   Liveness verified: "
    f"{result['liveness_verified']}"
)

print("   PASS")


print("7. Testing closed-eye frame 1...")

fake_detector.landmarks = closed_landmarks

result = service.process_frame(
    image
)

if result["blink_detected"]:
    raise RuntimeError(
        "Blink should not be detected "
        "after one closed frame."
    )

print("   PASS")


print("8. Testing closed-eye frame 2...")

result = service.process_frame(
    image
)

if result["blink_detected"]:
    raise RuntimeError(
        "Blink should not be detected "
        "while eyes remain closed."
    )

print("   PASS")


print("9. Testing eye reopening...")

fake_detector.landmarks = open_landmarks

result = service.process_frame(
    image
)

print(
    f"   Blink detected: "
    f"{result['blink_detected']}"
)

if not result["blink_detected"]:
    raise RuntimeError(
        "Blink should be detected "
        "when eyes reopen."
    )

print("   PASS")


print("10. Testing liveness verification...")

print(
    f"   Liveness verified: "
    f"{result['liveness_verified']}"
)

if not result["liveness_verified"]:
    raise RuntimeError(
        "Liveness should be verified "
        "after a confirmed blink."
    )

print("   PASS")


print("11. Checking blink count...")

print(
    f"   Blink count: "
    f"{result['blink_count']}"
)

if result["blink_count"] != 1:
    raise RuntimeError(
        "Blink count should be exactly 1."
    )

print("   PASS")


print("12. Testing reset...")

service.reset()

result = service.process_frame(
    image
)

if result["liveness_verified"]:
    raise RuntimeError(
        "Liveness should be reset."
    )

if result["blink_count"] != 0:
    raise RuntimeError(
        "Blink count should be reset to zero."
    )

print("   PASS")


print("13. Closing service...")

service.close()

print("   PASS")


print("ALL LIVENESS SERVICE TESTS PASSED")