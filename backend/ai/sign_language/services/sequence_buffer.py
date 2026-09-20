from collections import deque

import numpy as np


class SequenceBuffer:
    def __init__(
        self,
        sequence_length=30,
        feature_size=126,
    ):
        self.sequence_length = (
            sequence_length
        )

        self.feature_size = (
            feature_size
        )

        self.frames = deque(
            maxlen=sequence_length
        )

    def add(self, feature_vector):
        feature_vector = np.asarray(
            feature_vector,
            dtype=np.float32,
        )

        if feature_vector.shape != (
            self.feature_size,
        ):
            raise ValueError(
                "Expected feature vector "
                f"shape ({self.feature_size},), "
                f"got {feature_vector.shape}"
            )

        self.frames.append(
            feature_vector
        )

    def is_ready(self):
        return (
            len(self.frames)
            == self.sequence_length
        )

    def size(self):
        return len(self.frames)

    def get_sequence(self):
        if not self.is_ready():
            return None

        return np.stack(
            self.frames,
            axis=0,
        )

    def clear(self):
        self.frames.clear()