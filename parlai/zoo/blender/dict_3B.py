#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""
3B parameter Blender dictionary file: please see https://parl.ai/project/recipes.
"""

from .build import build

VERSION = "v1.0"


def download(datapath):
    build(datapath, "dict3B_v0.tgz", model_type="dict_3B", version=VERSION)
