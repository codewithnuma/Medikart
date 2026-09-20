from pathlib import Path
import time

import cv2
import mediapipe as mp

from backend.ai.sign_language.utils.landmark_utils import (
    extract_hand_vector,
)
from backend.ai.sign_language.services.sequence_buffer import (
    SequenceBuffer,
)

# ============================================================
# PATHS
# ============================================================

SIGN_LANGUAGE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    SIGN_LANGUAGE_DIR
    / "models"
    / "hand_landmarker.task"
)


# ============================================================
# HAND CONNECTIONS
# ============================================================

HAND_CONNECTIONS = [
    # Thumb
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),

    # Index
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),

    # Middle
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),

    # Ring
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),

    # Pinky
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),

    # Palm
    (0, 17),
]


# ============================================================
# DRAW HAND
# ============================================================

def draw_hand(frame, landmarks):
    height, width, _ = frame.shape

    points = []

    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)

        points.append((x, y))

    # Draw hand connections
    for start, end in HAND_CONNECTIONS:
        cv2.line(
            frame,
            points[start],
            points[end],
            (0, 255, 0),
            2,
        )

    # Draw landmarks
    for x, y in points:
        cv2.circle(
            frame,
            (x, y),
            4,
            (0, 0, 255),
            -1,
        )


# ============================================================
# MAIN
# ============================================================

def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    print(f"Using model: {MODEL_PATH}")

    BaseOptions = mp.tasks.BaseOptions

    HandLandmarker = (
        mp.tasks.vision.HandLandmarker
    )

    HandLandmarkerOptions = (
        mp.tasks.vision.HandLandmarkerOptions
    )

    RunningMode = (
        mp.tasks.vision.RunningMode
    )

    options = HandLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError(
            "Could not open webcam."
        )

    previous_timestamp = 0
    sequence_buffer = SequenceBuffer(
        sequence_length=30,
        feature_size=126,
    )
    print()
    print("Camera started.")
    print("Show your hand to the camera.")
    print("Press Q to close.")
    print()

    with HandLandmarker.create_from_options(
        options
    ) as landmarker:

        while True:
            success, frame = camera.read()

            if not success:
                print(
                    "Could not read webcam frame."
                )
                break

            # Mirror camera
            frame = cv2.flip(frame, 1)

            # OpenCV BGR -> MediaPipe RGB
            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB,
            )

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame,
            )

            timestamp_ms = int(
                time.monotonic() * 1000
            )

            if timestamp_ms <= previous_timestamp:
                timestamp_ms = (
                    previous_timestamp + 1
                )

            previous_timestamp = timestamp_ms

            result = landmarker.detect_for_video(
                mp_image,
                timestamp_ms,
            )

            hand_count = len(
                result.hand_landmarks
            )

            # ----------------------------------------
            # Convert hands into fixed 126-value vector
            # ----------------------------------------

            feature_vector = extract_hand_vector(
                result
            )

            if hand_count > 0:
                sequence_buffer.add(
                    feature_vector
                )
            else:
                sequence_buffer.clear()

            sequence = sequence_buffer.get_sequence()

            non_zero_values = int(
                (feature_vector != 0).sum()
            )

            if sequence is None:
                print(
                    "Buffer:",
                    sequence_buffer.size(),
                    "/ 30",
                )
            else:
                print(
                    "Sequence ready:",
                    sequence.shape,
                )

            print(
                "Vector shape:",
                feature_vector.shape,
                "| Non-zero:",
                non_zero_values,
                "| Hands:",
                hand_count,
            )

            # ----------------------------------------
            # Draw detected hands
            # ----------------------------------------

            for hand_landmarks in (
                result.hand_landmarks
            ):
                draw_hand(
                    frame,
                    hand_landmarks,
                )

            cv2.putText(
                frame,
                f"Hands detected: {hand_count}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                f"Vector: {feature_vector.shape}",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                "Press Q to exit",
                (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            cv2.imshow(
                "NirogNepal - Hand Tracking Test",
                frame,
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    camera.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()