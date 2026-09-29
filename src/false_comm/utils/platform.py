"""Platform detection and Linux-specific environment helpers."""

import os
import platform
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


class DistroInfo(NamedTuple):
    name: str
    version: str
    id: str
    is_linux: bool
    in_container: bool


def detect_distro() -> DistroInfo:
    """Detect operating system distribution with rich Linux inspection."""
    system = platform.system().lower()
    in_container = Path("/.dockerenv").exists() or _check_cgroup_container()

    if system != "linux":
        return DistroInfo(
            name=platform.system(),
            version=platform.release(),
            id=system,
            is_linux=False,
            in_container=in_container,
        )

    # Inspect /etc/os-release on Linux
    os_release = Path("/etc/os-release")
    name = "Linux"
    version = ""
    distro_id = "linux"

    if os_release.is_file():
        try:
            with open(os_release, encoding="utf-8") as f:
                data: dict[str, str] = {}
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        data[k.strip()] = v.strip().strip('"').strip("'")

                name = data.get("PRETTY_NAME") or data.get("NAME") or "Linux"
                version = data.get("VERSION_ID") or data.get("VERSION") or ""
                distro_id = data.get("ID") or "linux"
        except Exception:
            pass

    return DistroInfo(
        name=name,
        version=version,
        id=distro_id,
        is_linux=True,
        in_container=in_container,
    )


def _check_cgroup_container() -> bool:
    """Check if process is inside a container cgroup."""
    cgroup = Path("/proc/1/cgroup")
    if cgroup.is_file():
        try:
            text = cgroup.read_text(encoding="utf-8", errors="ignore")
            return any(x in text for x in ("docker", "lxc", "containerd", "kubepods"))
        except Exception:
            return False
    return False


def detect_linux_timezone() -> str:
    """Detect timezone in Git offset format (+0700, -0500) respecting Linux configs and TZ."""
    # 1. Check TZ environment variable if set
    tz_env = os.environ.get("TZ")
    if tz_env and hasattr(time, "tzset"):
        getattr(time, "tzset")()

    # 2. Check /etc/localtime symlink target on Linux
    localtime = Path("/etc/localtime")
    if localtime.is_symlink():
        try:
            target = os.readlink(str(localtime))
            if "zoneinfo/" in target:
                pass
        except Exception:
            pass

    # 3. Calculate exact current offset
    now = time.time()
    utc_offset_sec = datetime.fromtimestamp(now).astimezone().utcoffset()
    if utc_offset_sec is None:
        return "+0000"

    total_seconds = int(utc_offset_sec.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{sign}{hours:02d}{minutes:02d}"


def set_executable_permission(path: Path) -> None:
    """Set executable permission on Linux/Unix systems (chmod 755)."""
    if platform.system() != "Windows" and path.exists():
        try:
            current = path.stat().st_mode
            path.chmod(current | 0o755)
        except Exception:
            pass


def supports_unicode() -> bool:
    """Check if current terminal environment comfortably supports UTF-8."""
    encoding = (sys.stdout.encoding or "").lower()
    return "utf-8" in encoding or "utf8" in encoding
