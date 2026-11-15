# import cv2

# from backend.services.verification_session_service import (
#     VerificationSessionService,
# )


# def main():
#     print("=" * 60)
#     print("VERIFICATION SESSION WEBCAM TEST")
#     print("=" * 60)

#     session_service = VerificationSessionService()

#     session_id = session_service.create_session()

#     print(f"\nVerification session created:")
#     print(session_id)

#     camera = cv2.VideoCapture(0)

#     if not camera.isOpened():
#         print("\nERROR: Could not open webcam.")

#         session_service.close_session(session_id)
#         return

#     print("\nWebcam opened successfully.")
#     print("Look at the camera and blink naturally.")
#     print("Press Q to stop the test.")

#     try:
#         while True:
#             success, frame = camera.read()

#             if not success:
#                 print("ERROR: Could not read webcam frame.")
#                 break

#             result = session_service.process_frame(
#                 session_id,
#                 frame,
#             )

#             # Display information
#             status = (
#                 "VERIFIED"
#                 if result["verified"]
#                 else "NOT VERIFIED"
#             )

#             print(
#                 f"\r"
#                 f"Student: {result['student_id']} | "
#                 f"Similarity: {result['similarity']} | "
#                 f"Liveness: {result['liveness_verified']} | "
#                 f"Status: {status}    ",
#                 end="",
#             )

#             # Display webcam
#             cv2.imshow(
#                 "Verification Session Test",
#                 frame,
#             )

#             key = cv2.waitKey(1) & 0xFF

#             if key == ord("q"):
#                 break

#     finally:
#         camera.release()
#         cv2.destroyAllWindows()

#         session_service.close_session(
#             session_id
#         )

#         print("\n\nVerification session closed.")
#         print("Webcam released.")
#         print("=" * 60)


# if __name__ == "__main__":
#     main()











































import cv2

from backend.services.verification_session_service import (
    VerificationSessionService,
)


def main():
    print("=" * 70)
    print("VERIFICATION SESSION - WEBCAM + LIVENESS TEST")
    print("=" * 70)

    session_service = VerificationSessionService()

    session_id = session_service.create_session()

    print(f"\nVerification session created:")
    print(session_id)

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("\nERROR: Could not open webcam.")
        session_service.close_session(session_id)
        return

    print("\nWebcam opened successfully.")
    print("Look directly at the camera.")
    print("Blink naturally several times.")
    print("Press Q to stop the test.\n")

    frame_count = 0
    last_blink_count = 0

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("\nERROR: Could not read webcam frame.")
                break

            frame_count += 1

            result = session_service.process_frame(
                session_id,
                frame,
            )

            blink_count = result.get(
                "blink_count",
                0,
            )

            blink_detected = result.get(
                "blink_detected",
                False,
            )

            left_ear = result.get(
                "left_ear"
            )

            right_ear = result.get(
                "right_ear"
            )

            liveness_verified = result.get(
                "liveness_verified",
                False,
            )

            student_id = result.get(
                "student_id"
            )

            similarity = result.get(
                "similarity"
            )

            # Print when a new blink occurs.
            if blink_count > last_blink_count:
                print(
                    f"\nBLINK DETECTED!"
                    f"  Blink count: {blink_count}"
                )

                last_blink_count = blink_count

            # Print diagnostic information every 30 frames.
            if frame_count % 30 == 0:
                print(
                    f"\nFrames: {frame_count}"
                    f" | Student: {student_id}"
                    f" | Similarity: {similarity}"
                    f" | Left EAR: {left_ear}"
                    f" | Right EAR: {right_ear}"
                    f" | Blink count: {blink_count}"
                    f" | Liveness: {liveness_verified}"
                )

            # Add information to webcam window.
            cv2.putText(
                frame,
                f"Student: {student_id}",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Similarity: {similarity}",
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Blink Count: {blink_count}",
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"Liveness: {liveness_verified}",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

            cv2.imshow(
                "Verification Session Test",
                frame,
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    finally:
        camera.release()
        cv2.destroyAllWindows()

        session_service.close_session(
            session_id
        )

        print("\n")
        print("=" * 70)
        print("TEST FINISHED")
        print(f"Total frames processed: {frame_count}")
        print(f"Final blink count: {last_blink_count}")
        print("=" * 70)


if __name__ == "__main__":
    main()