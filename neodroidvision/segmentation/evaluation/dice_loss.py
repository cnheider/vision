from typing import Any

import numpy
import torch
from neodroidvision.segmentation.evaluation.f_score import f_score
from torch import nn

__all__ = ["dice_loss", "dice_coefficient", "DiceLoss", "BCEDiceLoss"]


def dice_coefficient(
    pred: torch.Tensor, target: torch.Tensor, *, epsilon: float = 1e-10
) -> torch.Tensor:
    """
This definition generalize to real valued pred and target vector.
This should be differentiable.
pred: tensor with first dimension as batch
target: tensor with first dimension as batch
"""

    pred_flat = pred.reshape(-1)
    target_flat = target.reshape(-1)

    intersection = 2.0 * (pred_flat * target_flat).sum() + epsilon
    union = (target_flat ** 2).sum() + (pred_flat ** 2).sum() + epsilon

    return intersection / union


def dice_loss(
    prediction: torch.Tensor, target: torch.Tensor, *, epsilon: float = 1e-10
) -> torch.Tensor:
    return 1 - dice_coefficient(prediction, target, epsilon=epsilon)


class DiceLoss(nn.Module):
    def __init__(self, *, eps: float = 1e-7, activation: callable = torch.sigmoid):
        super().__init__()
        self.activation = activation
        self.eps = eps

    def forward(self, y_pr: torch.Tensor, y_gt: torch.Tensor) -> torch.Tensor:
        return 1 - f_score(
            y_pr,
            y_gt,
            beta=1.0,
            eps=self.eps,
            threshold=None,
            activation=self.activation,
        )


class BCEDiceLoss(DiceLoss):
    def __init__(
        self,
        eps: float = 1e-7,
        activation: Any = None,
        lambda_dice: float = 1.0,
        lambda_bce: float = 1.0,
    ):
        super().__init__(eps=eps, activation=activation)

        if activation == None:
            self.bce = nn.BCELoss(reduction="mean")
        else:
            self.bce = nn.BCEWithLogitsLoss(reduction="mean")

        self.lambda_dice = lambda_dice
        self.lambda_bce = lambda_bce

    def forward(self, y_pr: torch.Tensor, y_gt: torch.Tensor) -> torch.Tensor:
        dice = super().forward(y_pr, y_gt)
        bce = self.bce(y_pr, y_gt)
        return (self.lambda_dice * dice) + (self.lambda_bce * bce)


if __name__ == "__main__":
    numpy.random.seed(2)
    data = numpy.random.random_sample((2, 1, 84, 84))
    GPU_STATS = torch.FloatTensor(data)
    b = torch.FloatTensor(data.transpose((0, 1, 3, 2)))
    print(dice_loss(GPU_STATS, GPU_STATS))
    print(dice_loss(GPU_STATS, b))

    h = torch.FloatTensor(numpy.array([[0, 1], [1, 1]]))
    j = torch.FloatTensor(numpy.ones((2, 2)))
    print(dice_loss(j, j))
