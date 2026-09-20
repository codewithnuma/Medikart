from pathlib import Path

import torch

from backend.ai.sign_language.model_architecture.st_gcn import (
    STGCN,
)
from backend.ai.sign_language.model_architecture.fc import (
    FC,
)
from backend.ai.sign_language.model_architecture.network import (
    Network,
)


# ============================================================
# PATHS
# ============================================================

SIGN_LANGUAGE_DIR = (
    Path(__file__).resolve().parents[1]
)

WEIGHTS_PATH = (
    SIGN_LANGUAGE_DIR
    / "models"
    / "ASL_citizen_stgcn_weights.pt"
)


# ============================================================
# MODEL SETTINGS
# ============================================================

NUM_CLASSES = 2731
NUM_FEATURES = 256


GRAPH_ARGS = {
    "num_nodes": 27,
    "center": 0,

    "inward_edges": [
        [2, 0],
        [1, 0],
        [0, 3],
        [0, 4],
        [3, 5],
        [4, 6],

        [5, 7],
        [6, 17],

        [7, 8],
        [7, 9],
        [9, 10],
        [7, 11],
        [11, 12],
        [7, 13],
        [13, 14],
        [7, 15],
        [15, 16],

        [17, 18],
        [17, 19],
        [19, 20],
        [17, 21],
        [21, 22],
        [17, 23],
        [23, 24],
        [17, 25],
        [25, 26],
    ],
}


# ============================================================
# LOAD MODEL
# ============================================================

def load_stgcn_model():
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"ST-GCN weights not found: {WEIGHTS_PATH}"
        )

    stgcn = STGCN(
        in_channels=2,
        graph_args=GRAPH_ARGS,
        edge_importance_weighting=True,
    )

    classifier = FC(
        n_features=NUM_FEATURES,
        num_class=NUM_CLASSES,
        dropout_ratio=0.05,
    )

    model = Network(
        encoder=stgcn,
        decoder=classifier,
    )

    # Microsoft's original model uses float64.
    model = model.double()

    state_dict = torch.load(
        WEIGHTS_PATH,
        map_location="cpu",
        weights_only=True,
    )

    model.load_state_dict(
        state_dict
    )

    model.eval()

    return model