from collections import deque

import numpy as np


class STGCNSequenceBuffer:
    def __init__(
        self,
        max_frames=128,
    ):
        self.max_frames = max_frames

        self.frames = deque(
            maxlen=max_frames
        )

    def add(self, keypoints):
        keypoints = np.asarray(
            keypoints,
            dtype=np.float32,
        )

        if keypoints.shape != (27, 2):
            raise ValueError(
                "Expected keypoints "
                f"shape (27, 2), "
                f"got {keypoints.shape}"
            )

        self.frames.append(
            keypoints
        )

    def size(self):
        return len(self.frames)

    def is_ready(self):
        return (
            len(self.frames)
            == self.max_frames
        )

    def get_sequence(self):
        if not self.is_ready():
            return None

        return np.stack(
            self.frames,
            axis=0,
        )

    def clear(self):
        self.frames.clear()