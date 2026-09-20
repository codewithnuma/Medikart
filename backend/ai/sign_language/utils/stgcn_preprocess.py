import numpy as np
import torch


MAX_FRAMES = 128


def preprocess_stgcn_sequence(
    sequence,
):
    """
    Input:
        sequence shape = (T, 27, 2)

    Output:
        tensor shape = (1, 2, 128, 27)
    """

    data = np.asarray(
        sequence,
        dtype=np.float64,
    )

    if data.ndim != 3:
        raise ValueError(
            "Expected sequence with shape "
            "(frames, 27, 2)"
        )

    if data.shape[1:] != (27, 2):
        raise ValueError(
            "Expected each frame to have "
            f"shape (27, 2), got {data.shape[1:]}"
        )

    length = data.shape[0]

    # ----------------------------------------
    # Downsample if longer than 128 frames
    # ----------------------------------------

    if length > MAX_FRAMES:
        indices = np.linspace(
            0,
            length - 1,
            MAX_FRAMES,
        ).astype(int)

        data = data[indices]

    # ----------------------------------------
    # Pad if shorter than 128 frames
    # ----------------------------------------

    elif length < MAX_FRAMES:
        padding = np.zeros(
            (
                MAX_FRAMES - length,
                27,
                2,
            ),
            dtype=np.float64,
        )

        data = np.concatenate(
            [
                data,
                padding,
            ],
            axis=0,
        )

    # ----------------------------------------
    # Shoulder normalization
    #
    # Our 27-point layout:
    # index 3 = left shoulder
    # index 4 = right shoulder
    # ----------------------------------------

    shoulder_left = data[:, 3, :]
    shoulder_right = data[:, 4, :]

    center = np.mean(
        (
            shoulder_left
            + shoulder_right
        )
        / 2.0,
        axis=0,
    )

    shoulder_distance = np.sqrt(
        (
            (
                shoulder_left
                - shoulder_right
            )
            ** 2
        ).sum(axis=-1)
    )

    mean_distance = np.mean(
        shoulder_distance
    )

    if mean_distance != 0:
        data = data - center
        data = data * (
            1.0 / mean_distance
        )

    # ----------------------------------------
    # Microsoft ST-GCN format:
    #
    # (frames, joints, coords)
    #        ↓
    # (coords, frames, joints)
    # ----------------------------------------

    data = np.transpose(
        data,
        (2, 0, 1),
    )

    tensor = torch.from_numpy(
        data
    ).double()

    # Add batch dimension
    tensor = tensor.unsqueeze(0)

    return tensor