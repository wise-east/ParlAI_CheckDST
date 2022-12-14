#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
"""
Simple agent which always outputs the given fixed response.

Good for debugging purposes or as a baseline, e.g. if always predicting a given class.
"""

from typing import Optional
from parlai.core.params import ParlaiParser
from parlai.core.opt import Opt
from parlai.core.agents import Agent
from parlai.core.message import Message


class FixedResponseAgent(Agent):
    @classmethod
    def add_cmdline_args(
        cls, parser: ParlaiParser, partial_opt: Optional[Opt] = None
    ) -> ParlaiParser:
        group = parser.add_argument_group("FixedResponse Arguments")
        group.add_argument(
            "-fr",
            "--fixed-response",
            type="nonestr",
            default="I don't know.",
            help="fixed response the agent always returns",
        )
        return parser

    def __init__(self, opt, shared=None):
        super().__init__(opt)
        self.id = "FixedResponseAgent"
        self.fixed_response = self.opt["fixed_response"]

    def act(self):
        return Message(
            {"id": self.getID(), "text": self.fixed_response, "episode_done": False}
        )
