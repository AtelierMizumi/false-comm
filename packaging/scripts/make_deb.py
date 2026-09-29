#!/usr/bin/env python3
"""Build a valid Debian .deb package without requiring dpkg-deb."""

import sys
import tarfile
import time
from pathlib import Path


def write_ar_member(f, name: str, data: bytes) -> None:
    name_field = f"{name:<16}"[:16].encode("ascii")
    mtime_field = f"{int(time.time()):<12}"[:12].encode("ascii")
    owner_field = b"0     "
    group_field = b"0     "
    mode_field = b"100644  "
    size_field = f"{len(data):<10}"[:10].encode("ascii")
    magic = b"`\n"
    f.write(name_field + mtime_field + owner_field + group_field + mode_field + size_field + magic)
    f.write(data)
    if len(data) % 2 != 0:
        f.write(b"\n")


def make_tar_gz(source_dir: Path, output_path: Path, arc_prefix: str = "") -> None:
    with tarfile.open(output_path, "w:gz") as tar:
        for p in source_dir.rglob("*"):
            rel = p.relative_to(source_dir)
            arcname = str(Path(arc_prefix) / rel) if arc_prefix else str(rel)
            tar.add(str(p), arcname=arcname)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: make_deb.py <deb_staging_dir> <output_deb_file>")
        sys.exit(1)

    deb_dir = Path(sys.argv[1]).resolve()
    output_deb = Path(sys.argv[2]).resolve()
    output_deb.parent.mkdir(parents=True, exist_ok=True)

    temp_dir = deb_dir.parent / "deb_build_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    control_tar = temp_dir / "control.tar.gz"
    data_tar = temp_dir / "data.tar.gz"

    # 1. Package DEBIAN/ into control.tar.gz
    make_tar_gz(deb_dir / "DEBIAN", control_tar)

    # 2. Package everything except DEBIAN/ into data.tar.gz
    with tarfile.open(data_tar, "w:gz") as tar:
        for item in deb_dir.iterdir():
            if item.name == "DEBIAN":
                continue
            for p in item.rglob("*"):
                rel = p.relative_to(deb_dir)
                tar.add(str(p), arcname=str(rel))

    # 3. Assemble standard UNIX AR archive
    with open(output_deb, "wb") as f:
        f.write(b"!<arch>\n")
        write_ar_member(f, "debian-binary", b"2.0\n")
        write_ar_member(f, "control.tar.gz", control_tar.read_bytes())
        write_ar_member(f, "data.tar.gz", data_tar.read_bytes())

    # Cleanup temp
    control_tar.unlink(missing_ok=True)
    data_tar.unlink(missing_ok=True)
    temp_dir.rmdir()
    print(f"✔ Debian package created successfully: {output_deb}")


if __name__ == "__main__":
    main()
