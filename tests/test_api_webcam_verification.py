import time

import cv2

from backend.services.verification_service import VerificationService


STUDENT_ID = "TEST_FACE_REG_001"


def main():
    print("=" * 60)
    print("REAL WEBCAM VERIFICATION TEST")
    print("=" * 60)

    verification_service = VerificationService()

    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        verification_service.close()
        raise RuntimeError("Could not open webcam.")

    print("\nWebcam opened successfully.")
    print("Look at the camera and blink naturally.")
    print("Press Q to stop the test.\n")

    verification_service.reset_liveness()

    verified = False
    start_time = time.time()

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("Could not read webcam frame.")
                continue

            result = verification_service.verify_frame(frame)

            student_id = result.get("student_id")
            similarity = result.get("similarity")
            liveness_verified = result.get("liveness_verified")

            print(
                f"\r"
                f"Student: {student_id} | "
                f"Similarity: {similarity} | "
                f"Liveness: {liveness_verified} | "
                f"Reason: {result.get('reason')}",
                end="",
                flush=True,
            )

            cv2.putText(
                frame,
                f"Student: {student_id}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Similarity: {similarity}",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Liveness: {liveness_verified}",
                (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.imshow(
                "API Webcam Verification Test",
                frame,
            )

            if result["verified"]:
                verified = True

                print("\n\n" + "=" * 60)
                print("VERIFICATION SUCCESSFUL")
                print("=" * 60)
                print(f"Student ID       : {student_id}")
                print(f"Similarity       : {similarity}")
                print("Face detected    : True")
                print("Face matched     : True")
                print("Liveness verified: True")
                print("=" * 60)

                time.sleep(2)
                break

            if time.time() - start_time > 60:
                print("\n\nVerification timed out after 60 seconds.")
                break

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("\n\nTest stopped by user.")
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()
        verification_service.close()

    print("\nCleanup completed.")

    if not verified:
        raise RuntimeError(
            "Real webcam verification was not completed successfully."
        )

    print("\nTEST PASSED")


if __name__ == "__main__":
    main()