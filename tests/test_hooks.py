# SPDX-FileCopyrightText: 2024 Datavolo Inc.
#
# SPDX-License-Identifier: Apache-2.0

from hatch_datavolo_nar.builder import NarBuilder
from hatch_datavolo_nar.hooks import hatch_register_builder


def test_hatch_register_builder():
    builder = hatch_register_builder()

    assert builder is NarBuilder
