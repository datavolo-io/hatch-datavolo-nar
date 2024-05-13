# SPDX-FileCopyrightText: 2024 Datavolo Inc.
#
# SPDX-License-Identifier: Apache-2.0

from hatchling.plugin import hookimpl

from hatch_datavolo_nar.builder import NarBuilder


@hookimpl
def hatch_register_builder():
    return NarBuilder
