#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
"""
MockTorchAgent.

Mean for unit testing purposes only, and should not be invoked otherwise.
"""

from typing import Optional
from parlai.core.params import ParlaiParser
from parlai.core.opt import Opt
from parlai.core.torch_agent import TorchAgent, Output
import torch
from parlai.core.agents import Agent


class MockDict(Agent):
    """
    Mock Dictionary Agent which just implements indexing and txt2vec.
    """

    null_token = "__null__"
    NULL_IDX = 0
    start_token = "__start__"
    BEG_IDX = 1001
    end_token = "__end__"
    END_IDX = 1002
    p1_token = "__p1__"
    P1_IDX = 2001
    p2_token = "__p2__"
    P2_IDX = 2002

    def __init__(self, opt, shared=None):
        """
        Initialize idx for incremental indexing.
        """
        self.idx = 0

    def __getitem__(self, key):
        """
        Return index of special token or return the token.
        """
        if key == self.null_token:
            return self.NULL_IDX
        elif key == self.start_token:
            return self.BEG_IDX
        elif key == self.end_token:
            return self.END_IDX
        elif key == self.p1_token:
            return self.P1_IDX
        elif key == self.p2_token:
            return self.P2_IDX
        else:
            self.idx += 1
            return self.idx

    def __setitem__(self, key, value):
        pass

    def __len__(self):
        return 0

    @classmethod
    def add_cmdline_args(
        cls, parser: ParlaiParser, partial_opt: Optional[Opt] = None
    ) -> ParlaiParser:
        """
        Add CLI args.
        """
        pass
        return parser

    def txt2vec(self, txt):
        """
        Return index of special tokens or range from 1 for each token.
        """
        self.idx = 0
        return [self[tok] for tok in txt.split()]

    def save(self, path, sort=False):
        """
        Override to do nothing.
        """
        pass


class MockTorchAgent(TorchAgent):
    """
    Use MockDict instead of regular DictionaryAgent.
    """

    @staticmethod
    def dictionary_class():
        """
        Replace normal dictionary class with mock one.
        """
        return MockDict

    def __init__(self, opt, shared=None):
        self.model = self.build_model()
        self.criterion = self.build_criterion()
        super().__init__(opt, shared)

    def build_model(self):
        return torch.nn.Module()

    def build_criterion(self):
        return torch.nn.NLLLoss()

    def train_step(self, batch):
        """
        Return confirmation of training.
        """
        return Output([f"Training {i}!" for i in range(batch.batchsize)])

    def eval_step(self, batch):
        """
        Return confirmation of evaluation.
        """
        return Output(
            [
                f"Evaluating {i} (responding to {batch.text_vec.tolist()})!"
                for i in range(batch.batchsize)
            ]
        )


class SilentTorchAgent(TorchAgent):
    """
    Use MockDict instead of regular DictionaryAgent.
    """

    @staticmethod
    def dictionary_class():
        """
        Replace normal dictionary class with mock one.
        """
        return MockDict

    def __init__(self, opt, shared=None):
        self.model = self.build_model()
        self.criterion = self.build_criterion()
        super().__init__(opt, shared)

    def build_model(self):
        return torch.nn.Module()

    def build_criterion(self):
        return torch.nn.NLLLoss()

    def train_step(self, batch):
        """
        Null output.
        """
        return Output()

    def eval_step(self, batch):
        """
        Null output.
        """
        return Output()


class MockTrainUpdatesAgent(MockTorchAgent):
    """
    Simulate training updates.
    """

    def train_step(self, batch):
        ret = super().train_step(batch)
        update_freq = self.opt.get("update_freq", 1)
        if update_freq == 1:
            self._number_training_updates += 1
        else:
            self._number_grad_accum = (self._number_grad_accum + 1) % update_freq
            self._number_training_updates += int(self._number_grad_accum == 0)
        return ret
