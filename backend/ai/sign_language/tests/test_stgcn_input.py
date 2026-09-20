from pathlib import Path
import time

import cv2
import mediapipe as mp

from backend.ai.sign_language.utils.stgcn_keypoints import (
    extract_stgcn_keypoints,
)
from backend.ai.sign_language.services.stgcn_sequence_buffer import (
    STGCNSequenceBuffer,
)

from backend.ai.sign_language.utils.stgcn_preprocess import (
    preprocess_stgcn_sequence,
)

from backend.ai.sign_language.services.stgcn_predictor import (
    STGCNPredictor,
)

# ============================================================
# PATHS
# ============================================================

SIGN_LANGUAGE_DIR = Path(__file__).resolve().parents[1]

HAND_MODEL_PATH = (
    SIGN_LANGUAGE_DIR
    / "models"
    / "hand_landmarker.task"
)

POSE_MODEL_PATH = (
    SIGN_LANGUAGE_DIR
    / "models"
    / "pose_landmarker_lite.task"
)


# ============================================================
# MAIN
# ============================================================

def main():
    BaseOptions = mp.tasks.BaseOptions

    HandLandmarker = (
        mp.tasks.vision.HandLandmarker
    )

    HandLandmarkerOptions = (
        mp.tasks.vision.HandLandmarkerOptions
    )

    PoseLandmarker = (
        mp.tasks.vision.PoseLandmarker
    )

    PoseLandmarkerOptions = (
        mp.tasks.vision.PoseLandmarkerOptions
    )

    RunningMode = (
        mp.tasks.vision.RunningMode
    )

    hand_options = HandLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=str(
                HAND_MODEL_PATH
            )
        ),
        running_mode=RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.3,
        min_hand_presence_confidence=0.3,
        min_tracking_confidence=0.3,
    )

    pose_options = PoseLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=str(
                POSE_MODEL_PATH
            )
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

    sequence_buffer = STGCNSequenceBuffer(
        max_frames=128,
    )
    predictor = STGCNPredictor()
    print()
    print("ST-GCN input test started.")
    print("Keep upper body and hands visible.")
    print("Press Q to close.")
    print()

    with (
        HandLandmarker.create_from_options(
            hand_options
        ) as hand_landmarker,
        PoseLandmarker.create_from_options(
            pose_options
        ) as pose_landmarker,
    ):

        while True:
            success, frame = camera.read()

            if not success:
                break

            # IMPORTANT:
            # Do not flip the frame before AI processing.
            # We want coordinates compatible with
            # the Microsoft training pipeline.

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

            if (
                timestamp_ms
                <= previous_timestamp
            ):
                timestamp_ms = (
                    previous_timestamp + 1
                )

            previous_timestamp = (
                timestamp_ms
            )

            hand_result = (
                hand_landmarker.detect_for_video(
                    mp_image,
                    timestamp_ms,
                )
            )

            pose_result = (
                pose_landmarker.detect_for_video(
                    mp_image,
                    timestamp_ms,
                )
            )

            keypoints = (
                extract_stgcn_keypoints(
                    pose_result,
                    hand_result,
                )
            )
            if (
                len(hand_result.hand_landmarks) > 0
                and len(pose_result.pose_landmarks) > 0
            ):
                sequence_buffer.add(
                    keypoints
                )
            else:
                sequence_buffer.clear()
            hand_count = len(
                hand_result.hand_landmarks
            )

            pose_detected = (
                len(
                    pose_result.pose_landmarks
                )
                > 0
            )
            sequence = sequence_buffer.get_sequence()

            if sequence is None:
                print(
                    "Buffer:",
                    sequence_buffer.size(),
                    "/ 128",
                )
            else:
                print(
                    "Sequence ready:",
                    sequence.shape,
                )
                model_input = preprocess_stgcn_sequence(
                    sequence
                )

                predictions = predictor.predict(
                    model_input,
                    top_k=5,
                )

                print()
                print("===== ASL PREDICTION =====")

                for prediction in predictions:
                    print(
                        prediction["gloss"],
                        f"{prediction['confidence'] * 100:.2f}%",
                    )

                print("==========================")
                print()

                sequence_buffer.clear()
            print(
                "ST-GCN:",
                keypoints.shape,
                "| Hands:",
                hand_count,
                "| Pose:",
                pose_detected,
            )

            cv2.putText(
                frame,
                f"ST-GCN input: {keypoints.shape}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                f"Hands: {hand_count}",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                f"Pose: {pose_detected}",
                (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
            )

            cv2.imshow(
                "NirogNepal - ST-GCN Input Test",
                frame,
            )

            if (
                cv2.waitKey(1)
                & 0xFF
                == ord("q")
            ):
                break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()