import time

import cv2
import requests


BASE_URL = "http://127.0.0.1:8000"

START_SESSION_URL = (
    f"{BASE_URL}/attendance/verify/start"
)

FRAME_URL = (
    f"{BASE_URL}/attendance/verify/frame"
)

ATTENDANCE_SESSION_ID = 11

# Send approximately 5 frames per second to the API.
FRAME_INTERVAL = 0.20


def create_verification_session():
    print("\nCreating verification session...")

    try:
        response = requests.post(
            START_SESSION_URL,
            params={
                "session_id": ATTENDANCE_SESSION_ID
            },
            timeout=10,
        )
    except requests.RequestException as error:
        print(
            f"ERROR: Could not connect to API: {error}"
        )
        return None

    if response.status_code != 200:
        print(
            "ERROR: Could not create verification session."
        )
        print(
            f"Status: {response.status_code}"
        )
        print(response.text)
        return None

    data = response.json()

    verification_session_id = data.get(
        "verification_session_id"
    )

    if not verification_session_id:
        print(
            "ERROR: API did not return "
            "verification_session_id."
        )
        return None

    print(
        "Verification session created successfully."
    )

    print(
        f"Verification Session ID: "
        f"{verification_session_id}"
    )

    return verification_session_id


def main():
    print("=" * 60)
    print("WEBCAM API VERIFICATION SESSION TEST")
    print("=" * 60)

    # -------------------------------------------------
    # Create fresh verification session
    # -------------------------------------------------

    verification_session_id = (
        create_verification_session()
    )

    if verification_session_id is None:
        return

    # -------------------------------------------------
    # Open webcam
    # -------------------------------------------------

    print("\nOpening webcam...")

    camera = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW,
    )

    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print(
            "ERROR: Could not open webcam."
        )
        return

    print(
        "Webcam opened successfully."
    )

    print("\nLook directly at the camera.")
    print(
        "Close both eyes deliberately for "
        "about 1 second, then open them."
    )
    print(
        "Repeat the blink several times."
    )
    print(
        "The test will run continuously."
    )
    print(
        "Press Q to stop."
    )
    print()

    captured_frames = 0
    sent_frames = 0
    successful_api_calls = 0

    last_send_time = 0
    last_print_time = 0

    last_blink_count = 0
    latest_verification = {}

    start_time = time.time()

    try:

        while True:

            # -------------------------------------------------
            # Capture webcam continuously
            # -------------------------------------------------

            success, frame = camera.read()

            if not success:
                print(
                    "\nERROR: Could not read webcam frame."
                )
                break

            captured_frames += 1

            current_time = time.time()

            # -------------------------------------------------
            # Send frames at controlled interval
            # -------------------------------------------------

            if (
                current_time - last_send_time
                >= FRAME_INTERVAL
            ):

                last_send_time = current_time
                sent_frames += 1

                encode_success, buffer = (
                    cv2.imencode(
                        ".jpg",
                        frame,
                    )
                )

                if not encode_success:
                    continue

                files = {
                    "image": (
                        "webcam.jpg",
                        buffer.tobytes(),
                        "image/jpeg",
                    )
                }

                params = {
                    "verification_session_id": (
                        verification_session_id
                    )
                }

                try:

                    response = requests.post(
                        FRAME_URL,
                        params=params,
                        files=files,
                        timeout=10,
                    )

                    if response.status_code != 200:

                        print(
                            f"\nAPI ERROR: "
                            f"{response.status_code}"
                        )

                        print(response.text)

                        continue

                    successful_api_calls += 1

                    data = response.json()

                    latest_verification = (
                        data.get(
                            "verification",
                            {},
                        )
                    )

                    # -------------------------------------------------
                    # Extract results
                    # -------------------------------------------------

                    student_id = (
                        latest_verification.get(
                            "student_id"
                        )
                    )

                    similarity = (
                        latest_verification.get(
                            "similarity"
                        )
                    )

                    left_ear = (
                        latest_verification.get(
                            "left_ear"
                        )
                    )

                    right_ear = (
                        latest_verification.get(
                            "right_ear"
                        )
                    )

                    blink_detected = (
                        latest_verification.get(
                            "blink_detected"
                        )
                    )

                    blink_count = (
                        latest_verification.get(
                            "blink_count",
                            0,
                        )
                    )

                    liveness_verified = (
                        latest_verification.get(
                            "liveness_verified"
                        )
                    )

                    verified = (
                        latest_verification.get(
                            "verified"
                        )
                    )

                    # -------------------------------------------------
                    # Detect blink count change
                    # -------------------------------------------------

                    if (
                        blink_count
                        != last_blink_count
                    ):

                        print(
                            "\n"
                            + "!" * 60
                        )

                        print(
                            "BLINK DETECTED!"
                        )

                        print(
                            f"Blink count: "
                            f"{blink_count}"
                        )

                        print(
                            f"Liveness verified: "
                            f"{liveness_verified}"
                        )

                        print(
                            f"Verified: "
                            f"{verified}"
                        )

                        print(
                            "!" * 60
                            + "\n"
                        )

                        last_blink_count = (
                            blink_count
                        )

                    # -------------------------------------------------
                    # Print diagnostics every second
                    # -------------------------------------------------

                    if (
                        current_time
                        - last_print_time
                        >= 1
                    ):

                        elapsed = (
                            current_time
                            - start_time
                        )

                        print(
                            f"Time: {elapsed:.1f}s | "
                            f"Captured: {captured_frames} | "
                            f"API: {successful_api_calls} | "
                            f"Student: {student_id} | "
                            f"Similarity: {similarity} | "
                            f"Left EAR: {left_ear} | "
                            f"Right EAR: {right_ear} | "
                            f"Blink: {blink_detected} | "
                            f"Count: {blink_count} | "
                            f"Liveness: {liveness_verified} | "
                            f"Verified: {verified}"
                        )

                        last_print_time = (
                            current_time
                        )

                except requests.RequestException as error:

                    print(
                        f"\nAPI connection error: "
                        f"{error}"
                    )

            # -------------------------------------------------
            # Display webcam
            # -------------------------------------------------

            blink_count = (
                latest_verification.get(
                    "blink_count",
                    0,
                )
            )

            liveness_verified = (
                latest_verification.get(
                    "liveness_verified",
                    False,
                )
            )

            verified = (
                latest_verification.get(
                    "verified",
                    False,
                )
            )

            student_id = (
                latest_verification.get(
                    "student_id"
                )
            )

            cv2.putText(
                frame,
                f"Blink Count: {blink_count}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Liveness: {liveness_verified}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Verified: {verified}",
                (20, 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            if student_id:
                cv2.putText(
                    frame,
                    f"Student: {student_id}",
                    (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

            cv2.imshow(
                "Webcam API Verification",
                frame,
            )

            # -------------------------------------------------
            # Quit
            # -------------------------------------------------

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    except KeyboardInterrupt:

        print(
            "\nTest interrupted by user."
        )

    finally:

        camera.release()
        cv2.destroyAllWindows()

        elapsed = time.time() - start_time

        print(
            "\n"
            + "=" * 60
        )

        print(
            "WEBCAM API VERIFICATION TEST FINISHED"
        )

        print(
            "=" * 60
        )

        print(
            f"Test duration: "
            f"{elapsed:.1f} seconds"
        )

        print(
            f"Total webcam frames captured: "
            f"{captured_frames}"
        )

        print(
            f"Frames sent to API: "
            f"{sent_frames}"
        )

        print(
            f"Successful API calls: "
            f"{successful_api_calls}"
        )

        print(
            f"Final blink count: "
            f"{last_blink_count}"
        )


if __name__ == "__main__":
    main()