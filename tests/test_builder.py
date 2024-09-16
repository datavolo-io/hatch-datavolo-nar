# SPDX-FileCopyrightText: 2024 Datavolo Inc.
#
# SPDX-License-Identifier: Apache-2.0

import datetime
import os
from pathlib import Path
from zipfile import ZipFile

import pytest
from hatchling.metadata.core import ProjectMetadata

from hatch_datavolo_nar.builder import NarBuilder


@pytest.fixture
def project_root(tmp_path):
    root_path = tmp_path / "root"
    root_path.mkdir()
    return root_path


@pytest.fixture
def project_name():
    return "processors"


@pytest.fixture
def project_version():
    return "1.0.0"


@pytest.fixture
def project_config(project_name, project_version):
    return {"name": project_name, "version": project_version}


@pytest.fixture
def project_metadata(project_config, project_root):
    return get_project_metadata(project_config, project_root)


@pytest.fixture
def builder(project_root, project_metadata):
    return NarBuilder(project_root, metadata=project_metadata)


@pytest.fixture
def dist_path(tmp_path: Path) -> Path:
    dist_path = tmp_path / "dist"
    dist_path.mkdir()
    return dist_path


def test_version_api(builder: NarBuilder):
    version_api = builder.get_version_api()
    assert version_api["standard"] is not None


def test_clean(builder: NarBuilder, dist_path: Path, project_name: str, project_version: str):
    nar_filename = get_nar_filename(project_name, project_version)
    dist_nar = dist_path.joinpath(nar_filename)

    dist_nar.touch()

    other_zip = dist_path.joinpath(f"{project_name}.zip")
    other_zip.touch()

    builder.clean(os.fspath(dist_path), [])

    assert not dist_nar.exists()
    assert other_zip.exists()


def test_build_standard(builder: NarBuilder, dist_path: Path, project_name: str, project_version: str):
    target_nar = builder.build_standard(dist_path.as_posix())

    nar_filename = get_nar_filename(project_name, project_version)
    expected_target_nar = dist_path / nar_filename
    assert target_nar == expected_target_nar.as_posix()

    with ZipFile(target_nar) as nar:
        nar.testzip()
        assert_manifest_found(nar, project_name, project_version)

        nar_entries = nar.namelist()
        assert "META-INF/" in nar_entries
        assert "NAR-INF/bundled-dependencies/" not in nar_entries


def test_build_with_dependencies(dist_path: Path, project_root: Path, project_name: str, project_version: str):
    project_config = {
        "name": project_name,
        "version": project_version,
        "dependencies": ["bech32==1.2.0", "json5==0.9.25"],
    }
    project_metadata = get_project_metadata(project_config, project_root)

    excluded_file = ".DS_Store"
    excluded_file_path = project_root / excluded_file
    excluded_file_path.touch()

    excluded_dir = "__pycache__"
    excluded_dir_path = project_root / excluded_dir
    excluded_dir_path.mkdir()

    source_dir = "src"
    project_source_path = project_root / source_dir
    project_source_path.mkdir()

    record_package = "record"
    record_package_path = project_source_path / record_package
    record_package_path.mkdir()

    record_processor_name = "RecordProcessor.py"

    record_processor = record_package_path / record_processor_name
    record_processor.touch()

    builder = NarBuilder(project_root.as_posix(), metadata=project_metadata)
    target_nar = builder.build_standard(dist_path.as_posix())

    nar_filename = get_nar_filename(project_name, project_version)
    expected_target_nar = dist_path / nar_filename
    assert target_nar == expected_target_nar.as_posix()

    with ZipFile(target_nar) as nar:
        nar.testzip()
        assert_manifest_found(nar, project_name, project_version)

        nar_entries = nar.namelist()

        assert f"{excluded_file}" not in nar_entries
        assert f"{excluded_dir}/" not in nar_entries

        assert f"{source_dir}/" in nar_entries
        assert f"{source_dir}/{record_package}/" in nar_entries
        assert f"{source_dir}/{record_package}/{record_processor_name}" in nar_entries
        assert "META-INF/" in nar_entries
        assert "NAR-INF/" in nar_entries
        assert "NAR-INF/bundled-dependencies/" in nar_entries
        assert "NAR-INF/bundled-dependencies/bech32/" in nar_entries
        assert "NAR-INF/bundled-dependencies/bech32/__init__.py" in nar_entries
        assert "NAR-INF/bundled-dependencies/json5/" in nar_entries
        assert "NAR-INF/bundled-dependencies/json5/__init__.py" in nar_entries

        meta_dir_info = nar.getinfo("META-INF/")

        expected_directory_mode = 0o755
        expected_external_attr = ((0o40000 | expected_directory_mode) & 0xFFFF) << 16 | 0x10
        assert meta_dir_info.external_attr == expected_external_attr

    cache_path = dist_path / "pip-cache"
    assert cache_path.is_dir()

    builder.clean(dist_path.as_posix(), [])

    assert not cache_path.is_dir()


def assert_manifest_found(nar: ZipFile, project_name: str, project_version: str):
    manifest_binary = nar.read("META-INF/MANIFEST.MF")
    manifest = str(manifest_binary, encoding="utf-8")

    now = datetime.datetime.now(datetime.UTC)
    partial_timestamp = now.strftime("%Y-%m-%dT")

    assert "Manifest-Version: 1.0" in manifest
    assert "Created-By: hatch-datavolo-nar" in manifest
    assert f"Build-Timestamp: {partial_timestamp}" in manifest
    assert f"Nar-Id: {project_name}-nar" in manifest
    assert f"Nar-Group: {project_name}" in manifest
    assert f"Nar-Version: {project_version}" in manifest


def get_nar_filename(project_name: str, project_version: str):
    return f"{project_name}-{project_version}.nar"


def get_project_metadata(project_config: dict, project_root: Path):
    hatch_config: dict = {
        "build": {
            "targets": {
                "datavolo-nar": {},
            },
        },
    }
    config = {
        "project": project_config,
        "tool": {
            "hatch": hatch_config,
        },
    }
    return ProjectMetadata(project_root.as_posix(), None, config=config)
