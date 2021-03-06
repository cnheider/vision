import argparse
from pathlib import Path
from typing import Sequence

import cv2
import numpy
import torch
from apppath import ensure_existence
from neodroid.environments.droid_environment import UnityEnvironment
from neodroid.utilities import extract_all_cameras
from neodroidvision import PROJECT_APP_PATH
from neodroidvision.detection import SingleShotDectection
from neodroidvision.detection.single_stage.ssd.bounding_boxes.ssd_transforms import (
    SSDTransform,
)
from neodroidvision.utilities import CheckPointer
from tqdm import tqdm
from warg import NOD

from draugr.opencv_utilities import draw_bounding_boxes, gamma_correct_float_to_byte
from draugr.torch_utilities import Split, TorchEvalSession, global_torch_device


@torch.no_grad()
def run_webcam_demo(
    cfg: NOD,
    categories: Sequence[str],
    model_ckpt: Path,
    score_threshold: float = 0.5,
    window_name: str = "SSD",
):
    """

:param categories:
:type categories:
:param cfg:
:type cfg:
:param model_ckpt:
:type model_ckpt:
:param score_threshold:
:type score_threshold:
:param window_name:
:type window_name:
:return:
:rtype:
"""

    cpu_device = torch.device("cpu")
    transforms = SSDTransform(
        cfg.input.image_size, cfg.input.pixel_mean, split=Split.Testing
    )
    model = SingleShotDectection(cfg)

    checkpointer = CheckPointer(
        model, save_dir=ensure_existence(PROJECT_APP_PATH.user_data / "results")
    )
    checkpointer.load(model_ckpt, use_latest=model_ckpt is None)
    print(
        f"Loaded weights from {model_ckpt if model_ckpt else checkpointer.get_checkpoint_file()}"
    )

    model.post_init()
    model.to(global_torch_device())

    with TorchEvalSession(model):
        for infos in tqdm(UnityEnvironment(connect_to_running=True)):
            info = next(iter(infos.values()))
            new_images = extract_all_cameras(info)
            image = next(iter(new_images.values()))[..., :3][..., ::-1]
            image = gamma_correct_float_to_byte(image)
            result = model(transforms(image)[0].unsqueeze(0).to(global_torch_device()))[
                0
            ]
            height, width, *_ = image.shape

            result["boxes"][:, 0::2] *= width / result["img_width"]
            result["boxes"][:, 1::2] *= height / result["img_height"]
            (boxes, labels, scores) = (
                result["boxes"].to(cpu_device).numpy(),
                result["labels"].to(cpu_device).numpy(),
                result["scores"].to(cpu_device).numpy(),
            )

            indices = scores > score_threshold

            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.imshow(
                window_name,
                draw_bounding_boxes(
                    image, boxes[indices], labels[indices], scores[indices], categories
                ).astype(numpy.uint8),
            )
            if cv2.waitKey(1) == 27:
                break  # esc to quit


def main():
    from configs.vgg_ssd300_coco_trainval35k import base_cfg

    parser = argparse.ArgumentParser(description="SSD Demo.")
    parser.add_argument(
        "--ckpt",
        type=str,
        default=PROJECT_APP_PATH.user_data / "ssd" / "models" /
                "mobilenet_v2_ssd320_voc0712.pth"
    # "mobilenet_v2_ssd320_voc0712.pth"
    # "vgg_ssd300_coco_trainval35k.pth"
    # "vgg_ssd512_coco_trainval35k.pth"
    ,
        help="Use weights from path",
    )
    parser.add_argument("--score_threshold", type=float, default=0.7)
    args = parser.parse_args()

    run_webcam_demo(
        cfg=base_cfg,
        categories=base_cfg.dataset_type.category_sizes,
        model_ckpt=Path(args.ckpt),
        score_threshold=args.score_threshold,
    )


if __name__ == "__main__":
    main()
