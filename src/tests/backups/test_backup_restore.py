"""
These tests are meant to be run from the host server,
prior to the execution of the backup.sh and restore.sh scripts.
"""

import os
import time
from typing import NamedTuple, Callable, Iterator, Protocol

import pytest
import subprocess

from pathlib import Path
from tempfile import TemporaryDirectory


def is_gnu_tar_installed():
    try:
        result = subprocess.run(
            ["tar", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return "GNU tar" in result.stdout
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not is_gnu_tar_installed(), reason="backup.sh and restore.sh require GNU tar to be installed."
)

SCRIPTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "scripts"


def create_test_files(directory: Path, filenames: list):
    """Create test files with simple content."""
    for name in filenames:
        path = directory / name
        with open(path, "w") as f:
            f.write(f"Content of {name}\n")


def call_backup_command(command: list[str], env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(command, env=env, check=True)


def call_restore_command(command: list[str], env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(command, env=env, input="y\n", text=True, check=True)


class RestoreFunc(Protocol):
    def __call__(self, level: int | None = None) -> subprocess.CompletedProcess:
        ...


class DataEnvironment(NamedTuple):
    backup: Callable[[], subprocess.CompletedProcess]
    restore: RestoreFunc
    file1: Path
    file2: Path


@pytest.fixture
def data_environment(tmp_path) -> Iterator[DataEnvironment]:
    """Sets up a temporary directory with files, and provides backup/restore commands.

    The directory structure created looks like:
      - temporary directory/
        - data/
          - original/
            - file1.txt (content: "Content of file1.txt\n")
            - file2.txt (content: "Content of file2.txt\n")
        - backups/

    The files are accessible as `file1` and `file2`.
    The `backup()` function calls the backup script with no arguments and environment variables set.
    The `restore(level)` function calls the restore script, optionally for a specific level,
      with environment variables set.
    """
    cycle_length = 2
    data_name = "original"

    backup_command = ["bash", str(SCRIPTS_PATH / "backup.sh"), data_name, str(cycle_length)]
    restore_command = ["bash", str(SCRIPTS_PATH / "restore.sh"), data_name, "0"]

    file_directory = tmp_path / "data" / data_name
    file_directory.mkdir(parents=True)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True)

    env = os.environ.copy()
    env["ENV_MODE"] = "testing"
    env["DATA_PATH"] = str(tmp_path / "data")
    env["BACKUP_PATH"] = str(backup_dir)

    def backup() -> subprocess.CompletedProcess:
        return call_backup_command(backup_command, env)

    def restore(level: int | None = None) -> subprocess.CompletedProcess:
        level_args = ["--level", str(level)] if level is not None else []
        return call_restore_command(restore_command + level_args, env)

    file1 = file_directory / "file1.txt"
    file1.write_text("Content of file1.txt\n")
    file2 = file_directory / "file2.txt"
    file2.write_text("Content of file2.txt\n")

    yield DataEnvironment(backup, restore, file1, file2)


def test_backup_happy_path():
    """
    Test if the backup.sh script generates the correct directory structure.
    Usage: `bash backup.sh <data to backup:str> <cycle length:int>`
    """
    with TemporaryDirectory() as tmpdir:
        cycle_length = 2
        data_name = "original"

        data_dir = tmpdir / Path("data")
        original_dir = tmpdir / Path("data") / data_name
        backup_dir = tmpdir / Path("backups")
        env = os.environ.copy()
        env["ENV_MODE"] = "testing"
        env["DATA_PATH"] = str(data_dir)
        env["BACKUP_PATH"] = str(backup_dir)

        os.makedirs(original_dir)
        os.makedirs(backup_dir)
        create_test_files(original_dir, ["file1.txt", "file2.txt"])

        backup_cycle_0_path = backup_dir / data_name / f"{data_name}_0"
        backup_cycle_1_path = backup_dir / data_name / f"{data_name}_1"
        files_in_cycle_0 = [
            backup_cycle_0_path / f"{data_name}0.tar.gz",
            backup_cycle_0_path / f"{data_name}1.tar.gz",
            backup_cycle_0_path / f"{data_name}.snar",
        ]
        files_in_cycle_1 = [
            backup_cycle_1_path / f"{data_name}0.tar.gz",
            backup_cycle_1_path / f"{data_name}.snar",
        ]

        backup_command = ["bash", SCRIPTS_PATH / "backup.sh", data_name, str(cycle_length)]

        for i in range(cycle_length + 1):
            call_backup_command(backup_command, env)

        for backup_file in files_in_cycle_1 + files_in_cycle_0:
            assert backup_file.exists()


def test_restore_happy_path(data_environment: DataEnvironment):
    """
    Test if the restore.sh script restores the files properly.
    Usage:
    `bash restore.sh <data to restore:str> <cycle label:int> [--level|-l <level:int>]`
    """
    backup, restore, file1, file2 = data_environment

    assert file1.read_text() == "Content of file1.txt\n"
    assert file2.read_text() == "Content of file2.txt\n"

    backup()
    file1.unlink()
    file2.write_text("Content of new file\n")
    time.sleep(0.1)  # See #387

    backup()
    microsecond = 10**-6
    time.sleep(microsecond)  # See #387
    restore()

    assert not file1.exists(), f"{file1} shouldn't be here."
    assert file2.exists(), f"{file2} should be here."
    assert "Content of new file\n" in file2.read_text()

    restore(level=0)
    assert file1.exists(), f"{file1} should be here."
    assert file2.exists(), f"{file2} should be here."

    restore(level=1)
    assert not file1.exists(), f"{file1} shouldn't be here."
