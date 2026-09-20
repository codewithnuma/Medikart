from pathlib import Path
import time

import cv2
import mediapipe as mp


SIGN_LANGUAGE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    SIGN_LANGUAGE_DIR
    / "models"
    / "pose_landmarker_lite.task"
)


POSE_CONNECTIONS = [
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
]


def draw_pose(frame, landmarks):
    height, width, _ = frame.shape

    points = []

    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)

        points.append((x, y))

    for start, end in POSE_CONNECTIONS:
        cv2.line(
            frame,
            points[start],
            points[end],
            (255, 255, 0),
            2,
        )

    for index in [
        0,
        2,
        5,
        11,
        12,
        13,
        14,
    ]:
        x, y = points[index]

        cv2.circle(
            frame,
            (x, y),
            5,
            (0, 255, 255),
            -1,
        )


def main():
    BaseOptions = mp.tasks.BaseOptions
    PoseLandmarker = (
        mp.tasks.vision.PoseLandmarker
    )
    PoseLandmarkerOptions = (
        mp.tasks.vision.PoseLandmarkerOptions
    )
    RunningMode = (
        mp.tasks.vision.RunningMode
    )

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError(
            "Could not open webcam."
        )

    previous_timestamp = 0

    print("Pose camera started.")
    print("Keep your upper body visible.")
    print("Press Q to close.")

    with PoseLandmarker.create_from_options(
        options
    ) as landmarker:

        while True:
            success, frame = camera.read()

            if not success:
                break

            frame = cv2.flip(frame, 1)

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

            pose_count = len(
                result.pose_landmarks
            )

            if pose_count > 0:
                draw_pose(
                    frame,
                    result.pose_landmarks[0],
                )

            cv2.putText(
                frame,
                f"Pose detected: {pose_count}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )

            cv2.imshow(
                "NirogNepal - Pose Test",
                frame,
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()