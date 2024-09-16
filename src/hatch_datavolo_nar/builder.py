# SPDX-FileCopyrightText: 2024 Datavolo Inc.
#
# SPDX-License-Identifier: Apache-2.0

import datetime
import io
import os
import sys
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from shlex import quote
from shutil import rmtree
from subprocess import PIPE, check_call
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from hatchling.builders.config import BuilderConfig
from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.builders.utils import normalize_archive_path
from hatchling.metadata.core import ProjectMetadata


class NarBundle:
    DIRECTORY_MODE = 0o755

    BUILD_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

    def __init__(self, zip_descriptor: ZipFile):
        self.zip_descriptor = zip_descriptor
        self.directories_added: list[str] = []

    def add_entry(self, path: Path, archive_name: str) -> None:
        normalized_archive_name = normalize_archive_path(archive_name)

        parents = reversed(Path(normalized_archive_name).parents)
        for parent_dir in parents:
            parent_dir_name = str(parent_dir)
            if parent_dir_name == ".":
                continue

            if parent_dir_name not in self.directories_added:
                self.mkdir(parent_dir_name)
                self.directories_added.append(parent_dir_name)

        self.zip_descriptor.write(path, normalized_archive_name)

    def mkdir(self, directory_name: str) -> None:
        directory_mode = self.DIRECTORY_MODE
        self.zip_descriptor.mkdir(directory_name, mode=directory_mode)

    def write_manifest(self, metadata: ProjectMetadata) -> None:
        manifest_dir = "META-INF"
        self.mkdir(manifest_dir)

        current_timestamp = datetime.datetime.now(datetime.UTC)
        build_timestamp = current_timestamp.strftime(self.BUILD_TIMESTAMP_FORMAT)

        manifest_lines = [
            "Manifest-Version: 1.0",
            "Created-By: hatch-datavolo-nar",
            f"Build-Timestamp: {build_timestamp}",
            f"Nar-Id: {metadata.core.raw_name}-nar",
            f"Nar-Group: {metadata.core.raw_name}",
            f"Nar-Version: {metadata.version}",
        ]

        manifest = io.StringIO()
        for line in manifest_lines:
            manifest.write(line)
            manifest.write("\n")

        archive_name = f"{manifest_dir}/MANIFEST.MF"
        self.zip_descriptor.writestr(archive_name, manifest.getvalue())

    @classmethod
    @contextmanager
    def open_bundle(cls, target: Path) -> Generator:
        with ZipFile(target, mode="w", compression=ZIP_DEFLATED) as zip_descriptor:
            yield cls(zip_descriptor)


class NarBuilder(BuilderInterface):
    PLUGIN_NAME = "nar"

    def get_version_api(self) -> dict[str, Callable[..., str]]:
        return {"standard": self.build_standard}

    @classmethod
    def get_config_class(cls) -> type[BuilderConfig]:
        return BuilderConfig

    def clean(self, directory: str, _versions: list[str]) -> None:
        cache_dir = Path(self.get_cache_dir(directory))
        if cache_dir.is_dir():
            rmtree(cache_dir)

        for filename in os.listdir(directory):
            if filename.endswith(".nar"):
                os.remove(os.path.join(directory, filename))

    def build_standard(self, build_directory: str, **_build_data: Any) -> str:
        project_name = self.normalize_file_name_component(self.metadata.core.raw_name)
        target_nar = Path(build_directory, f"{project_name}-{self.metadata.version}.nar")

        with NarBundle.open_bundle(target_nar) as nar:
            nar.write_manifest(self.metadata)

            for included_file in self.recurse_included_files():
                included_file_path = Path(included_file.path)
                nar.add_entry(included_file_path, included_file.distribution_path)

            if self.metadata.core.dependencies:
                self.app.display_waiting("Processing dependencies...")
                self.process_dependencies(build_directory, nar)

        return os.fspath(target_nar)

    def process_dependencies(self, build_directory: str, nar: NarBundle) -> None:
        nar_inf_dir = "NAR-INF"
        bundled_dependencies_dir = f"{nar_inf_dir}/bundled-dependencies"

        cache_dir = self.get_cache_dir(build_directory)
        dependencies_dir = Path(f"{build_directory}/{bundled_dependencies_dir}")
        self.install_dependencies(dependencies_dir, cache_dir)

        installed_dependencies = Path(dependencies_dir).glob("**/*")
        installed_dependency: Path
        for installed_dependency in installed_dependencies:
            if installed_dependency.is_dir():
                continue

            archive_name = str(installed_dependency.relative_to(build_directory))
            nar.add_entry(installed_dependency, archive_name)

        nar_dependencies_dir = Path(f"{build_directory}/{nar_inf_dir}")
        rmtree(nar_dependencies_dir)

    def install_dependencies(self, directory: Path, cache_dir: str) -> None:
        self.app.display_waiting("Loading dependencies")

        install_arguments = [
            sys.executable,
            "-m",
            "pip",
            "install",
        ]

        install_arguments.extend(quote(dependency) for dependency in self.metadata.core.dependencies)

        additional_arguments = [
            "--upgrade",
            "--no-python-version-warning",
            "--no-input",
            "--cache-dir",
            quote(cache_dir),
            "--quiet",
            "--target",
            quote(str(directory.absolute())),
        ]

        install_arguments.extend(additional_arguments)
        check_call(install_arguments, stdout=PIPE, stderr=PIPE, shell=False)

    def get_cache_dir(self, build_directory: str) -> str:
        return f"{build_directory}/pip-cache"
