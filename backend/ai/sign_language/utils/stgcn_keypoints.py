import numpy as np


# Microsoft ASL Citizen ST-GCN uses:
#
# 7 pose points:
# 0, 2, 5, 11, 12, 13, 14
#
# 10 points from each hand:
# 0, 4, 5, 8, 9, 12, 13, 16, 17, 20

POSE_INDICES = [
    0,
    2,
    5,
    11,
    12,
    13,
    14,
]

HAND_INDICES = [
    0,
    4,
    5,
    8,
    9,
    12,
    13,
    16,
    17,
    20,
]


def _extract_hand_points(
    hand_result,
):
    left_hand = np.zeros(
        (10, 2),
        dtype=np.float32,
    )

    right_hand = np.zeros(
        (10, 2),
        dtype=np.float32,
    )

    for index, landmarks in enumerate(
        hand_result.hand_landmarks
    ):
        if index >= len(
            hand_result.handedness
        ):
            continue

        hand_name = (
            hand_result
            .handedness[index][0]
            .category_name
            .lower()
        )

        selected = np.array(
            [
                [
                    landmarks[i].x,
                    landmarks[i].y,
                ]
                for i in HAND_INDICES
            ],
            dtype=np.float32,
        )

        if hand_name == "left":
            left_hand = selected

        elif hand_name == "right":
            right_hand = selected

    return left_hand, right_hand


def extract_stgcn_keypoints(
    pose_result,
    hand_result,
):
    """
    Returns shape:

    (27, 2)

    Order:
    7 pose
    + 10 left hand
    + 10 right hand
    """

    pose_points = np.zeros(
        (7, 2),
        dtype=np.float32,
    )

    if pose_result.pose_landmarks:
        pose_landmarks = (
            pose_result.pose_landmarks[0]
        )

        pose_points = np.array(
            [
                [
                    pose_landmarks[i].x,
                    pose_landmarks[i].y,
                ]
                for i in POSE_INDICES
            ],
            dtype=np.float32,
        )

    left_hand, right_hand = (
        _extract_hand_points(
            hand_result
        )
    )

    keypoints = np.concatenate(
        [
            pose_points,
            left_hand,
            right_hand,
        ],
        axis=0,
    )

    return keypoints