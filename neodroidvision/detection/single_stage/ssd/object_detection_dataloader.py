#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Christian Heider Nielsen"
__doc__ = r"""

           Created on 22/03/2020
           """

from pathlib import Path
from typing import List, Union

import torch
from data.detection.multi_dataset import MultiDataset
from neodroidvision.utilities import (
    BatchCollator,
    DistributedSampler,
    LimitedBatchResampler,
)
from torch.utils.data import ConcatDataset, DataLoader
from warg import NOD

from draugr.torch_utilities import Split

__all__ = ["object_detection_data_loaders"]


def object_detection_data_loaders(
    *,
    data_root: Path,
    cfg: NOD,
    split: Split = Split.Training,
    distributed: bool = False,
    max_iter: int = None,
    start_iter: int = 0
) -> Union[List[DataLoader], DataLoader]:
    """

:param data_root:
:type data_root:
:param cfg:
:type cfg:
:param split:
:type split:
:param distributed:
:type distributed:
:param max_iter:
:type max_iter:
:param start_iter:
:type start_iter:
:return:
:rtype:
"""

    shuffle = split == Split.Training or distributed
    data_loaders = []

    for dataset in MultiDataset(
        cfg=cfg,
        dataset_type=cfg.dataset_type,
        data_root=data_root,
        sub_datasets=cfg.datasets.train
        if split == Split.Training
        else cfg.datasets.test,
        split=split,
    ).sub_datasets:
        if distributed:
            sampler = DistributedSampler(dataset, shuffle=shuffle)
        elif shuffle:
            sampler = torch.utils.data.RandomSampler(dataset)
        else:
            sampler = torch.utils.data.sampler.SequentialSampler(dataset)

        batch_sampler = torch.utils.data.sampler.BatchSampler(
            sampler=sampler,
            batch_size=cfg.solver.batch_size
            if split == Split.Training
            else cfg.test.batch_size,
            drop_last=False,
        )
        if max_iter is not None:
            batch_sampler = LimitedBatchResampler(
                batch_sampler, num_iterations=max_iter, start_iter=start_iter
            )

        data_loaders.append(
            DataLoader(
                dataset,
                num_workers=cfg.data_loader.num_workers,
                batch_sampler=batch_sampler,
                pin_memory=cfg.data_loader.pin_memory,
                collate_fn=BatchCollator(split == Split.Training),
            )
        )

    if split == Split.Training:
        # during training, a single (possibly concatenated) data_loader is returned
        assert len(data_loaders) == 1
        return data_loaders[0]

    return data_loaders
