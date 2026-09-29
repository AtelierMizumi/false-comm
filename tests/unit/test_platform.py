"""Unit tests for Linux and platform detection utilities."""

import platform
import stat
from pathlib import Path

from false_comm.utils.platform import (
    detect_distro,
    detect_linux_timezone,
    set_executable_permission,
    supports_unicode,
)


def test_detect_distro() -> None:
    distro = detect_distro()
    assert distro.name
    assert isinstance(distro.is_linux, bool)
    if platform.system().lower() == "linux":
        assert distro.is_linux is True


def test_detect_linux_timezone() -> None:
    tz = detect_linux_timezone()
    assert len(tz) == 5
    assert tz[0] in ("+", "-")
    assert tz[1:].isdigit()


def test_set_executable_permission(tmp_path: Path) -> None:
    test_sh = tmp_path / "test_script.sh"
    test_sh.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")

    set_executable_permission(test_sh)
    if platform.system() != "Windows":
        mode = test_sh.stat().st_mode
        assert bool(mode & stat.S_IXUSR)


def test_supports_unicode() -> None:
    # Function should execute without errors and return boolean
    res = supports_unicode()
    assert isinstance(res, bool)
