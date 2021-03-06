#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Christian Heider Nielsen"
__doc__ = r"""

           Created on 22/03/2020
           """

"""Get the binarized MNIST dataset and convert to hdf5.
From https://github.com/yburda/iwae/blob/master/datasets.py
"""
import os
import urllib.request

import h5py
import numpy
from neodroidvision import PROJECT_APP_PATH


def parse_binary_mnist(data_dir):
    def lines_to_np_array(lines):
        return numpy.array([[int(i) for i in line.split()] for line in lines])

    with open(os.path.join(data_dir, "binarized_mnist_train.amat")) as f:
        lines = f.readlines()
    train_data = lines_to_np_array(lines).astype("float32")
    with open(os.path.join(data_dir, "binarized_mnist_valid.amat")) as f:
        lines = f.readlines()
    validation_data = lines_to_np_array(lines).astype("float32")
    with open(os.path.join(data_dir, "binarized_mnist_test.amat")) as f:
        lines = f.readlines()
    test_data = lines_to_np_array(lines).astype("float32")
    return train_data, validation_data, test_data


def download_binary_mnist(
    fname="binary_mnist.h5",
    data_dir=(PROJECT_APP_PATH.user_data / "vanilla_vae" / "data"),
):
    if not data_dir.exists():
        data_dir.mkdir(parents=True)
    subdatasets = ["train", "valid", "test"]
    for subdataset in subdatasets:
        filename = f"binarized_mnist_{subdataset}.amat"
        url = (
            f"http://www.cs.toronto.edu/~larocheh/public/datasets/binarized_mnist"
            f"/binarized_mnist_{subdataset}.amat"
        )
        local_filename = str(data_dir / filename)
        urllib.request.urlretrieve(url, local_filename)

    train, validation, test = parse_binary_mnist(data_dir)

    data_dict = {"train": train, "valid": validation, "test": test}
    f = h5py.File(fname, "w")
    f.create_dataset("train", data=data_dict["train"])
    f.create_dataset("valid", data=data_dict["valid"])
    f.create_dataset("test", data=data_dict["test"])
    f.close()
    print(f"Saved binary MNIST data to: {fname}")


if __name__ == "__main__":
    download_binary_mnist()
