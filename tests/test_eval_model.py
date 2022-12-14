#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import os
from parlai.utils.io import PathManager
import pytest
import unittest
import parlai.utils.testing as testing_utils
from parlai.scripts.eval_model import get_task_world_logs


class TestEvalModel(unittest.TestCase):
    """
    Basic tests on the eval_model.py example.
    """

    def test_noevalmode(self):
        """
        Ensure you get an error trying to use eval_model with -dt train.
        """
        with self.assertRaises(ValueError):
            testing_utils.eval_model(
                {"task": "integration_tests", "model": "repeat_label"},
                valid_datatype="train",
            )

    def test_evalmode(self):
        """
        Eval_model with -dt train:evalmode should be okay.
        """
        testing_utils.eval_model(
            {"task": "integration_tests", "model": "repeat_label"},
            valid_datatype="train:evalmode",
        )

    def test_output(self):
        """
        Test output of running eval_model.
        """
        opt = dict(
            task="integration_tests",
            model="repeat_label",
            datatype="valid",
            num_examples=5,
            display_examples=False,
        )

        valid, test = testing_utils.eval_model(opt)

        self.assertEqual(valid["accuracy"], 1)
        self.assertEqual(test["accuracy"], 1)
        self.assertNotIn("rouge_L", valid)
        self.assertNotIn("rouge_L", test)

    # TODO: install py-rouge in fbcode and unmark this test
    @pytest.mark.nofbcode
    def test_metrics_all(self):
        """
        Test output of running eval_model.
        """
        opt = dict(
            task="integration_tests",
            model="repeat_label",
            datatype="valid",
            num_examples=5,
            display_examples=False,
            metrics="all",
        )

        valid, test = testing_utils.eval_model(opt)

        self.assertEqual(valid["accuracy"], 1)
        self.assertEqual(valid["rouge_L"], 1)
        self.assertEqual(valid["rouge_1"], 1)
        self.assertEqual(valid["rouge_2"], 1)
        self.assertEqual(test["accuracy"], 1)
        self.assertEqual(test["rouge_L"], 1)
        self.assertEqual(test["rouge_1"], 1)
        self.assertEqual(test["rouge_2"], 1)

    # TODO: install py-rouge in fbcode and unmark this test
    @pytest.mark.nofbcode
    def test_metrics_select(self):
        """
        Test output of running eval_model.
        """
        opt = dict(
            task="integration_tests",
            model="repeat_label",
            datatype="valid",
            num_examples=5,
            display_examples=False,
            metrics="accuracy,rouge",
        )

        valid, test = testing_utils.eval_model(opt)

        self.assertEqual(valid["accuracy"], 1)
        self.assertEqual(valid["rouge_L"], 1)
        self.assertEqual(valid["rouge_1"], 1)
        self.assertEqual(valid["rouge_2"], 1)
        self.assertEqual(test["accuracy"], 1)
        self.assertEqual(test["rouge_L"], 1)
        self.assertEqual(test["rouge_1"], 1)
        self.assertEqual(test["rouge_2"], 1)

        self.assertNotIn("bleu-4", valid)
        self.assertNotIn("bleu-4", test)

    def test_multitasking_metrics_macro(self):
        valid, test = testing_utils.eval_model(
            {
                "task": "integration_tests:candidate,"
                "integration_tests:multiturnCandidate",
                "model": "random_candidate",
                "aggregate_micro": False,
            }
        )

        task1_acc = valid["integration_tests:candidate/accuracy"]
        task2_acc = valid["integration_tests:multiturnCandidate/accuracy"]
        total_acc = valid["accuracy"]
        # task 2 is 4 times the size of task 1
        self.assertEqual(
            total_acc,
            (task1_acc.value() + task2_acc.value()) * 0.5,
            "Task accuracy is averaged incorrectly",
        )

        valid, test = testing_utils.eval_model(
            {
                "task": "integration_tests:candidate,"
                "integration_tests:multiturnCandidate",
                "model": "random_candidate",
                "aggregate_micro": False,
            }
        )
        task1_acc = valid["integration_tests:candidate/accuracy"]
        task2_acc = valid["integration_tests:multiturnCandidate/accuracy"]
        total_acc = valid["accuracy"]

        # metrics are combined correctly
        self.assertEqual(
            total_acc,
            (task1_acc.value() + task2_acc.value()) * 0.5,
            "Task accuracy is averaged incorrectly",
        )

    def test_multitasking_metrics_micro(self):
        valid, test = testing_utils.eval_model(
            {
                "task": "integration_tests:candidate,"
                "integration_tests:multiturnCandidate",
                "model": "random_candidate",
                "aggregate_micro": True,
            }
        )

        task1_acc = valid["integration_tests:candidate/accuracy"]
        task2_acc = valid["integration_tests:multiturnCandidate/accuracy"]
        total_acc = valid["accuracy"]
        # task 2 is 4 times the size of task 1
        self.assertEqual(
            total_acc, task1_acc + task2_acc, "Task accuracy is averaged incorrectly"
        )

        valid, test = testing_utils.eval_model(
            {
                "task": "integration_tests:candidate,"
                "integration_tests:multiturnCandidate",
                "model": "random_candidate",
                "aggregate_micro": True,
            }
        )
        task1_acc = valid["integration_tests:candidate/accuracy"]
        task2_acc = valid["integration_tests:multiturnCandidate/accuracy"]
        total_acc = valid["accuracy"]

        # metrics are combined correctly
        self.assertEqual(
            total_acc, (task1_acc + task2_acc), "Task accuracy is averaged incorrectly"
        )

    def test_train_evalmode(self):
        """
        Test that evaluating a model with train:evalmode completes an epoch.
        """
        base_dict = {"model": "repeat_label", "datatype": "train:evalmode"}

        teachers = ["integration_tests:fixed_dialog_candidate", "integration_tests"]
        batchsize = [1, 64]
        for bs in batchsize:
            for teacher in teachers:
                d = base_dict.copy()
                d["task"] = teacher
                d["batchsize"] = bs
                with testing_utils.timeout(time=20):
                    valid, test = testing_utils.eval_model(
                        d, valid_datatype=d["datatype"]
                    )
                self.assertEqual(
                    int(valid["exs"]),
                    500,
                    f"train:evalmode failed with bs {bs} and teacher {teacher}",
                )

    def test_save_report(self):
        """
        Test that we can save report from eval model.
        """
        with testing_utils.tempdir() as tmpdir:
            log_report = os.path.join(tmpdir, "world_logs.jsonl")
            save_report = os.path.join(tmpdir, "report")
            opt = dict(
                task="integration_tests",
                model="repeat_label",
                datatype="valid",
                batchsize=97,
                display_examples=False,
                world_logs=log_report,
                report_filename=save_report,
            )
            valid, test = testing_utils.eval_model(opt)

            with PathManager.open(log_report) as f:
                json_lines = f.readlines()
            assert len(json_lines) == 100

    def test_save_multiple_logs(self):
        """
        Test that we can save multiple world_logs from eval model on multiple tasks.
        """
        with testing_utils.tempdir() as tmpdir:
            log_report = os.path.join(tmpdir, "world_logs.jsonl")
            save_report = os.path.join(tmpdir, "report")
            multitask = "integration_tests,blended_skill_talk"
            opt = dict(
                task=multitask,
                model="repeat_label",
                datatype="valid",
                batchsize=97,
                num_examples=100,
                display_examples=False,
                world_logs=log_report,
                report_filename=save_report,
            )
            valid, test = testing_utils.eval_model(opt)

            for task in multitask.split(","):
                task_log_report = get_task_world_logs(
                    task, log_report, is_multitask=True
                )
                with PathManager.open(task_log_report) as f:
                    json_lines = f.readlines()
                assert len(json_lines) == 100


if __name__ == "__main__":
    unittest.main()
