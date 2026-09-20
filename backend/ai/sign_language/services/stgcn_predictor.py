import torch

from backend.ai.sign_language.services.stgcn_model import (
    load_stgcn_model,
)

from backend.ai.sign_language.services.label_service import (
    load_class_labels,
    get_gloss,
)


class STGCNPredictor:
    def __init__(self):
        print(
            "Loading ASL ST-GCN model..."
        )

        self.model = (
            load_stgcn_model()
        )

        self.labels = (
            load_class_labels()
        )

        print(
            "ASL ST-GCN model ready."
        )

    def predict(
        self,
        tensor,
        top_k=5,
    ):
        """
        tensor shape:
        (1, 2, 128, 27)
        """

        if tensor.shape != (
            1,
            2,
            128,
            27,
        ):
            raise ValueError(
                "Expected tensor shape "
                "(1, 2, 128, 27), "
                f"got {tuple(tensor.shape)}"
            )

        with torch.no_grad():
            logits = self.model(
                tensor
            )

            probabilities = (
                torch.softmax(
                    logits,
                    dim=1,
                )
            )

            values, indices = (
                torch.topk(
                    probabilities,
                    k=top_k,
                    dim=1,
                )
            )

        predictions = []

        for confidence, index in zip(
            values[0],
            indices[0],
        ):
            class_index = (
                index.item()
            )

            predictions.append(
                {
                    "class_index":
                        class_index,

                    "gloss":
                        get_gloss(
                            class_index,
                            self.labels,
                        ),

                    "confidence":
                        confidence.item(),
                }
            )

        return predictions