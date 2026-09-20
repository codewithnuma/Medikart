import numpy as np


LANDMARKS_PER_HAND = 21
COORDINATES_PER_LANDMARK = 3

HAND_VECTOR_SIZE = (
    LANDMARKS_PER_HAND
    * COORDINATES_PER_LANDMARK
)

TOTAL_VECTOR_SIZE = (
    HAND_VECTOR_SIZE * 2
)


def _flatten_hand(
    landmarks,
):
    """
    Convert 21 hand landmarks into
    [x, y, z, x, y, z, ...]
    """

    values = []

    for landmark in landmarks:
        values.extend(
            [
                landmark.x,
                landmark.y,
                landmark.z,
            ]
        )

    return np.array(
        values,
        dtype=np.float32,
    )


def extract_hand_vector(
    result,
):
    """
    Returns a fixed 126-value vector:

    first 63 values  = left hand
    second 63 values = right hand

    Missing hands are filled with zeros.
    """

    left_hand = np.zeros(
        HAND_VECTOR_SIZE,
        dtype=np.float32,
    )

    right_hand = np.zeros(
        HAND_VECTOR_SIZE,
        dtype=np.float32,
    )

    for index, landmarks in enumerate(
        result.hand_landmarks
    ):

        if (
            index
            >= len(result.handedness)
        ):
            continue

        handedness = (
            result.handedness[index][0]
        )

        hand_name = (
            handedness.category_name
            .lower()
        )

        vector = _flatten_hand(
            landmarks
        )

        if hand_name == "left":
            left_hand = vector

        elif hand_name == "right":
            right_hand = vector

    return np.concatenate(
        [
            left_hand,
            right_hand,
        ]
    )