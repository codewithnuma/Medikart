import json
from pathlib import Path


SIGN_LANGUAGE_DIR = (
    Path(__file__).resolve().parents[1]
)

LABELS_PATH = (
    SIGN_LANGUAGE_DIR
    / "models"
    / "class_labels.json"
)


def load_class_labels():
    if not LABELS_PATH.exists():
        raise FileNotFoundError(
            f"Class labels not found: {LABELS_PATH}"
        )

    with open(
        LABELS_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def get_gloss(
    class_index,
    labels=None,
):
    if labels is None:
        labels = load_class_labels()

    return labels.get(
        str(class_index),
        "UNKNOWN",
    )