# hatch-datavolo-nar

This project provides a [Builder](https://hatch.pypa.io/latest/plugins/builder/reference/) plugin
for the [Hatch](https://hatch.pypa.io/latest/) Python project manager that enables building packaged
archives for [Apache NiFi](https://nifi.apache.org). The NAR format uses the
[ZIP](https://en.wikipedia.org/wiki/ZIP_(file_format)) file structure, containing a manifest
and NiFi components with dependencies.

[![pypi](https://img.shields.io/pypi/v/hatch-datavolo-nar.svg)](https://pypi.org/project/hatch-datavolo-nar/)
[![python-versions](https://img.shields.io/pypi/pyversions/hatch-datavolo-nar.svg)](https://pypi.org/project/hatch-datavolo-nar/)
[![build](https://github.com/datavolo-io/hatch-datavolo-nar/actions/workflows/build.yml/badge.svg)](https://github.com/datavolo-io/hatch-datavolo-nar/actions/workflows/build.yml)
[![license](https://img.shields.io/github/license/datavolo-io/hatch-datavolo-nar)](https://github.com/datavolo-io/hatch-datavolo-nar/blob/main/LICENSE)
[![Hatch](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://github.com/python/mypy)

## Integrating

This project requires the [Hatch](https://hatch.pypa.io/latest/) project manager for Python with
a working [pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
configuration.

### Build System

The `hatch-datavolo-nar` library must be added to the `build-system.requires` field in a
[pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) configuration
for Hatch to load the plugin.

```toml
[build-system]
requires = ["hatchling", "hatch-datavolo-nar"]
build-backend = "hatchling.build"
```

### Build Packages

The `hatch-datavolo-nar` plugin reads the Hatch
[build configuration](https://hatch.pypa.io/latest/config/build/) to select files for packaging.

The `nar` build target should be configured with a `packages` field that identifies the directory
containing Python files to be included.

The following configuration section provides an example for a project containing a `processors` package
using the [src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
for directory organization:

```toml
[tool.hatch.build.targets.nar]
packages = ["src/processors"]
```

### Build Command

The `hatch-datavolo-nar` plugin provides the `nar` build target, which can be invoked using the Hatch build command.

```shell
hatch build -t nar
```

A Python NAR with platform-specific dependencies requires building on a machine with the same architecture as the runtime system.

## Developing

Run the following Hatch command to build the project:

```shell
hatch build
```

The Python wheel can be referenced using a file URI in a project build system.

```toml
[build-system]
requires = ["hatchling", "hatch-datavolo-nar@file:///dist/hatch_datavolo_nar-0.1.0-py3-none-any.whl"]
build-backend = "hatchling.build"
```

The Hatch build environment caches build plugins, which requires pruning existing environments to use a new version of the plugin.

```shell
hatch env prune
```

### Coding Conventions

This project uses the following tools to evaluate adherence to coding conventions:

- [Coverage.py](https://coverage.readthedocs.io) for code coverage
- [mypy](https://www.mypy-lang.org/) for typing
- [Ruff](https://docs.astral.sh/ruff/) for formatting

## Versioning

This project follows the [Semantic Versioning Specification 2.0.0](https://semver.org/).

## Licensing

This project is distributed under the terms of the
[Apache License 2.0](https://spdx.org/licenses/Apache-2.0.html).
