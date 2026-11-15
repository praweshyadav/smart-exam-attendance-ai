import time

import cv2

from backend.ai.liveness_detector import LivenessDetector
from backend.ai.blink_detector import BlinkDetector


print("===== GUIDED WEBCAM BLINK CALIBRATION =====")
print("Press Q at any time to quit.")


# -------------------------------------------------
# Configuration
# -------------------------------------------------

OPEN_DURATION = 3
CLOSED_DURATION = 2
NATURAL_BLINK_DURATION = 10
REPETITIONS = 3

BLINK_THRESHOLD = 0.15
MIN_CLOSED_FRAMES = 2


# -------------------------------------------------
# Camera
# -------------------------------------------------

print("1. Opening webcam...")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    raise RuntimeError(
        "Could not open webcam."
    )

print("   PASS")


# -------------------------------------------------
# AI components
# -------------------------------------------------

print("2. Creating liveness components...")

liveness_detector = LivenessDetector()

blink_detector = BlinkDetector(
    blink_threshold=BLINK_THRESHOLD,
    min_closed_frames=MIN_CLOSED_FRAMES,
)

print("   PASS")


minimum_ear = float("inf")
maximum_ear = 0.0

quit_requested = False


def draw_text(
    frame,
    text,
    position,
    scale=0.8,
    thickness=2,
):
    """
    Draw text on the webcam frame.
    """

    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (0, 255, 0),
        thickness,
    )


def show_frame(
    frame,
    instruction,
    remaining=None,
):
    """
    Display webcam frame with instructions.
    """

    display_frame = frame.copy()

    if remaining is not None:

        draw_text(
            display_frame,
            instruction,
            (20, 40),
            0.75,
            2,
        )

        draw_text(
            display_frame,
            f"Time remaining: {remaining:.1f}s",
            (20, 80),
            0.75,
            2,
        )

    else:

        draw_text(
            display_frame,
            instruction,
            (20, 40),
            0.75,
            2,
        )

    cv2.imshow(
        "Guided Webcam Blink Calibration",
        display_frame,
    )

    key = cv2.waitKey(1) & 0xFF

    return key


def run_phase(
    instruction,
    duration,
):
    """
    Run one guided calibration phase.
    """

    global minimum_ear
    global maximum_ear
    global quit_requested

    start_time = time.time()

    while True:

        elapsed = time.time() - start_time

        if elapsed >= duration:
            break

        success, frame = camera.read()

        if not success:
            print("Failed to read webcam frame.")
            quit_requested = True
            return

        results = liveness_detector.process_frame(
            frame
        )

        remaining = duration - elapsed

        display_frame = frame.copy()

        draw_text(
            display_frame,
            instruction,
            (20, 40),
            0.75,
            2,
        )

        draw_text(
            display_frame,
            f"Time remaining: {remaining:.1f}s",
            (20, 80),
            0.75,
            2,
        )

        if results.face_landmarks:

            landmarks = results.face_landmarks[0]

            blink_result = (
                blink_detector.process_landmarks(
                    landmarks
                )
            )

            left_ear = blink_result["left_ear"]
            right_ear = blink_result["right_ear"]
            average_ear = blink_result["average_ear"]

            minimum_ear = min(
                minimum_ear,
                average_ear,
            )

            maximum_ear = max(
                maximum_ear,
                average_ear,
            )

            draw_text(
                display_frame,
                f"Left EAR: {left_ear:.3f}",
                (20, 125),
                0.65,
                2,
            )

            draw_text(
                display_frame,
                f"Right EAR: {right_ear:.3f}",
                (20, 160),
                0.65,
                2,
            )

            draw_text(
                display_frame,
                f"Average EAR: {average_ear:.3f}",
                (20, 195),
                0.65,
                2,
            )

            draw_text(
                display_frame,
                f"Blink Count: {blink_result['blink_count']}",
                (20, 230),
                0.65,
                2,
            )

        else:

            draw_text(
                display_frame,
                "NO FACE DETECTED",
                (20, 125),
                0.7,
                2,
            )

        cv2.imshow(
            "Guided Webcam Blink Calibration",
            display_frame,
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            quit_requested = True
            return


try:

    print()
    print("Get ready.")
    print("Look directly at the camera.")
    print()

    # -------------------------------------------------
    # Countdown
    # -------------------------------------------------

    for countdown in [3, 2, 1]:

        success, frame = camera.read()

        if not success:
            quit_requested = True
            break

        display_frame = frame.copy()

        draw_text(
            display_frame,
            "GET READY",
            (20, 50),
            1.0,
            3,
        )

        draw_text(
            display_frame,
            f"Starting in {countdown}",
            (20, 100),
            0.9,
            2,
        )

        cv2.imshow(
            "Guided Webcam Blink Calibration",
            display_frame,
        )

        key = cv2.waitKey(1000) & 0xFF

        if key == ord("q"):
            quit_requested = True
            break

    # -------------------------------------------------
    # Calibration repetitions
    # -------------------------------------------------

    if not quit_requested:

        for repetition in range(
            1,
            REPETITIONS + 1,
        ):

            print(
                f"Calibration {repetition}/{REPETITIONS}"
            )

            # -----------------------------------------
            # Open eyes
            # -----------------------------------------

            print(
                "  Keep your eyes OPEN."
            )

            run_phase(
                f"OPEN YOUR EYES - Round {repetition}",
                OPEN_DURATION,
            )

            if quit_requested:
                break

            # -----------------------------------------
            # Close eyes
            # -----------------------------------------

            print(
                "  CLOSE BOTH EYES completely."
            )

            run_phase(
                f"CLOSE BOTH EYES - Round {repetition}",
                CLOSED_DURATION,
            )

            if quit_requested:
                break

            # -----------------------------------------
            # Reopen eyes
            # -----------------------------------------

            print(
                "  OPEN YOUR EYES."
            )

            run_phase(
                f"OPEN YOUR EYES - Round {repetition}",
                OPEN_DURATION,
            )

            if quit_requested:
                break

    # -------------------------------------------------
    # Natural blinking phase
    # -------------------------------------------------

    if not quit_requested:

        print()
        print(
            "Now blink naturally for "
            f"{NATURAL_BLINK_DURATION} seconds."
        )

        run_phase(
            "BLINK NATURALLY",
            NATURAL_BLINK_DURATION,
        )

    # -------------------------------------------------
    # Results
    # -------------------------------------------------

    print()
    print("===== CALIBRATION RESULTS =====")

    print(
        f"Total blinks detected: "
        f"{blink_detector.blink_count}"
    )

    if minimum_ear != float("inf"):

        print(
            f"Minimum EAR observed: "
            f"{minimum_ear:.6f}"
        )

        print(
            f"Maximum EAR observed: "
            f"{maximum_ear:.6f}"
        )

    print()
    print("Calibration complete.")

    # Keep result visible for a few seconds.

    while not quit_requested:

        success, frame = camera.read()

        if not success:
            break

        display_frame = frame.copy()

        draw_text(
            display_frame,
            "CALIBRATION COMPLETE",
            (20, 50),
            0.9,
            3,
        )

        draw_text(
            display_frame,
            f"Blinks: {blink_detector.blink_count}",
            (20, 100),
            0.7,
            2,
        )

        if minimum_ear != float("inf"):

            draw_text(
                display_frame,
                f"Minimum EAR: {minimum_ear:.3f}",
                (20, 140),
                0.7,
                2,
            )

            draw_text(
                display_frame,
                f"Maximum EAR: {maximum_ear:.3f}",
                (20, 180),
                0.7,
                2,
            )

        draw_text(
            display_frame,
            "Press Q to exit.",
            (20, 230),
            0.7,
            2,
        )

        cv2.imshow(
            "Guided Webcam Blink Calibration",
            display_frame,
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break


finally:

    camera.release()

    cv2.destroyAllWindows()

    liveness_detector.close()

    print()
    print("Webcam released.")
    print(
        f"Final blink count: "
        f"{blink_detector.blink_count}"
    )

    if minimum_ear != float("inf"):

        print(
            f"Final minimum EAR: "
            f"{minimum_ear:.6f}"
        )

        print(
            f"Final maximum EAR: "
            f"{maximum_ear:.6f}"
        )

    print("GUIDED BLINK CALIBRATION FINISHED")