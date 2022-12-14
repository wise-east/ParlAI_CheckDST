#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from parlai.core.image_featurizers import ImageLoader
from parlai.core.metrics import TeacherMetrics
from parlai.core.teachers import Teacher
from parlai.utils.io import PathManager
from .build import build

import json
import random
import os


def _path(opt):
    build(opt)

    questions_path = os.path.join(
        opt["datapath"], "FVQA", "new_dataset_release", "all_qs_dict_release.json"
    )
    trainset_path = os.path.join(opt["datapath"], "FVQA", "Name_Lists")
    image_path = os.path.join(
        opt["datapath"], "FVQA", "new_dataset_release", "images", ""
    )

    return questions_path, trainset_path, image_path


class SplitTeacher(Teacher):
    """
    FVQA Teacher, which loads the json VQA data and implements its own `act` method for
    interacting with student agent.

    Use "fvqa:split:X" to choose between splits 0-4 (inclusive), or just "fvqa" to use
    the default split (0).
    """

    def __init__(self, opt, shared=None):
        super().__init__(opt)

        dt = opt["datatype"].split(":")[0]
        if dt not in ("train", "test"):
            raise RuntimeError("Not valid datatype (only train/test).")

        task = opt.get("task", "fvqa:split:0")
        task_num = 0  # default to train/split 0
        split = task.split(":")
        if len(split) > 2:
            task_num = split[2]
            if task_num not in [str(i) for i in range(5)]:
                raise RuntimeError("Invalid train/test split ID (0-4 inclusive)")

        if not hasattr(self, "factmetrics"):
            if shared and shared.get("factmetrics"):
                self.factmetrics = shared["factmetrics"]
            else:
                self.factmetrics = TeacherMetrics(opt.get("metrics", "default"))
            self.datatype = opt["datatype"]
        questions_path, trainset_path, self.image_path = _path(opt)

        if shared and "ques" in shared:
            self.ques = shared["ques"]
        else:
            self._setup_data(questions_path, trainset_path, dt, task_num)
        self.len = len(self.ques)

        self.asked_question = False
        # for ordered data in batch mode (especially, for validation and
        # testing), each teacher in the batch gets a start index and a step
        # size so they all process disparate sets of the data
        self.step_size = opt.get("batchsize", 1)
        self.data_offset = opt.get("batchindex", 0)
        self.image_loader = ImageLoader(opt)

        self.reset()

    def num_examples(self):
        return self.len

    def num_episodes(self):
        return self.len

    def report(self):
        r = super().report()
        for k, v in self.factmetrics.report().items():
            r[f"factmetrics_{k}"] = v
        return r

    def reset(self):
        # Reset the dialog so that it is at the start of the epoch,
        # and all metrics are reset.
        super().reset()
        self.lastY = None
        self.episode_idx = self.data_offset - self.step_size
        self.epochDone = False

    def reset_metrics(self):
        super().reset_metrics()
        self.factmetrics.clear()

    def observe(self, observation):
        """
        Process observation for metrics.
        """
        if self.lastY is not None:
            if self.asked_question:
                self.metrics.evaluate_response(observation, self.lastY[0])
            else:
                self.factmetrics.evaluate_response(observation, self.lastY[1])
                self.lastY = None
        return observation

    def act(self):
        if self.asked_question:
            self.asked_question = False
            action = {"text": "Which fact supports this answer?", "episode_done": True}
            if self.datatype.startswith("train"):
                action["labels"] = self.lastY[1]
            if (
                self.datatype != "train"
                and self.episode_idx + self.step_size >= self.num_episodes()
            ):
                self.epochDone = True
            return action

        if self.datatype == "train":
            self.episode_idx = random.randrange(self.len)
        else:
            self.episode_idx = (self.episode_idx + self.step_size) % self.num_episodes()

        self.asked_question = True
        qa = self.ques[self.episode_idx]
        question = qa["question"]
        img_path = self.image_path + qa["img_file"]

        action = {
            "image": self.image_loader.load(img_path),
            "text": question,
            "episode_done": False,
        }

        human_readable = qa["fact_surface"].replace("[", "").replace("]", "")
        self.lastY = [[qa["answer"]], [human_readable]]

        if self.datatype.startswith("train"):
            action["labels"] = self.lastY[0]

        return action

    def share(self):
        shared = super().share()
        shared["factmetrics"] = self.factmetrics
        shared["ques"] = self.ques
        if hasattr(self, "facts"):
            shared["facts"] = self.facts
        return shared

    def _setup_data(self, questions_path, trainset_path, datatype, task_num):
        print("loading: " + questions_path)
        with PathManager.open(questions_path) as questions_file:
            questions = json.load(questions_file)
        train_test_images = set()
        fn = os.path.join(trainset_path, "{}_list_{}.txt".format(datatype, task_num))
        with PathManager.open(fn) as imageset:
            for line in imageset:
                train_test_images.add(line.strip())
        self.ques = [
            questions[k]
            for k in sorted(questions.keys())
            if questions[k]["img_file"] in train_test_images
        ]


class DefaultTeacher(SplitTeacher):
    pass
