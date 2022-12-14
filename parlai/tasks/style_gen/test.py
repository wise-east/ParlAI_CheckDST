#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from parlai.utils.testing import AutoTeacherTest  # noqa: F401


class TestBlendedSkillTalkTeacher(AutoTeacherTest):
    task = "style_gen:labeled_blended_skill_talk"


class TestConvAI2Teacher(AutoTeacherTest):
    task = "style_gen:labeled_convAI2_persona_topicifier"


class TestEDTeacher(AutoTeacherTest):
    task = "style_gen:labeled_ED_persona_topicifier"


class TestWoWTeacher(AutoTeacherTest):
    task = "style_gen:labeled_WoW_persona_topicifier"
