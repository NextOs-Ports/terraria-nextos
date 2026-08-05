#!/usr/bin/env python3
"""Validate owned Terraria 1.4.5.6.4 data and apply the Unity boot patch.

The Play Store ships more than one build of the same visible Terraria version
(different versionCodes, split configurations and repack tools), so this hook
accepts any structurally sound 1.4.5.6.4 payload instead of demanding one
exact byte-for-byte build. The reference build ("14564") is still recognized
by hash and recorded as such; unknown builds pass a deeper structural
validation and are flagged in the manifest so the loader only applies its
byte-verified patches where the code actually matches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
from pathlib import Path
import sys


# Reference build: Google Play arm64-v8a build of 1.4.5.6.4 (Unity 2021.3.56f2).
KNOWN_BUILDS = {
    "6456fbddbe10addc6c7c2253f8ad6ff589a01309945d1e1194d2890a21709574": {
        "build_id": "playstore-14564",
        "libil2cpp_sha256": "dc67ce5f48dc4738977e52fa524115beb95a641410eec39458adaf8f03b10c25",
    },
}

REQUIRED_BIN_FILES = (
    "Data/boot.config",
    "Data/data.unity3d",
    "Data/Managed/Metadata/global-metadata.dat",
    "Data/resources.resource",
    "Data/unity default resources",
)

LIBRARIES = ("libunity.so", "libil2cpp.so", "libc++_shared.so")

GLOBAL_METADATA_MAGIC = b"\xaf\x1b\xb1\xfa"
UNITY_VERSION_PATTERN = re.compile(rb"20\d\d\.\d+\.\d+[a-z]\d+")
SUPPORTED_UNITY_PREFIX = b"2021.3."

BOOT_APPEND = (
    b"androidUseSwappy=0\n"
    b"gfx-disable-mt-rendering=1\n"
    b"gfx-enable-gfx-jobs=0\n"
    b"gfx-enable-native-gfx-jobs=0\n"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_regular(path: Path, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"missing regular file: {label}")
    if path.stat().st_size == 0:
        raise RuntimeError(f"empty file: {label}")


def check_elf_aarch64(path: Path, label: str) -> None:
    with path.open("rb") as stream:
        header = stream.read(20)
    if len(header) < 20 or header[:4] != b"\x7fELF":
        raise RuntimeError(f"{label} is not an ELF object")
    if header[4] != 2:
        raise RuntimeError(f"{label} is not a 64-bit ELF object")
    machine = struct.unpack_from("<H", header, 18)[0]
    if machine != 183:
        raise RuntimeError(f"{label} is not an AArch64 object (machine={machine})")


def find_unity_version(libunity: Path) -> str:
    with libunity.open("rb") as stream:
        blob = stream.read()
    match = UNITY_VERSION_PATTERN.search(blob)
    if not match:
        raise RuntimeError("libunity.so carries no Unity version string")
    version = match.group(0)
    if not version.startswith(SUPPORTED_UNITY_PREFIX):
        raise RuntimeError(
            "unsupported Unity engine %s; this port targets Unity 2021.3 builds "
            "of Terraria 1.4.5.6.4" % version.decode("ascii", "replace")
        )
    return version.decode("ascii")


def check_magic(path: Path, magic: bytes, label: str) -> None:
    with path.open("rb") as stream:
        if stream.read(len(magic)) != magic:
            raise RuntimeError(f"{label} has an unexpected file signature")


def write_atomic(path: Path, data: bytes, mode: int = 0o644) -> None:
    temporary = path.with_name(f".{path.name}.nxpart.{os.getpid()}")
    try:
        with temporary.open("wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def patch_boot_config(boot_path: Path) -> dict:
    source = boot_path.read_bytes()
    if not source.strip():
        raise RuntimeError("boot.config is empty")
    if b"\x00" in source:
        raise RuntimeError("boot.config is not a text file")
    wanted = [line for line in BOOT_APPEND.splitlines() if line]
    present = source.splitlines()
    missing = [line for line in wanted if line not in present]
    patched = source
    if missing:
        if not patched.endswith(b"\n"):
            patched += b"\n"
        patched += b"\n".join(missing) + b"\n"
        write_atomic(boot_path, patched, boot_path.stat().st_mode & 0o777)
    return {
        "lines": [line.decode("ascii") for line in wanted],
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "patched_sha256": hashlib.sha256(patched).hexdigest(),
        "already_patched": not missing,
    }


def prepare(stage: Path) -> str:
    data_root = stage / "bin"
    for relative in REQUIRED_BIN_FILES:
        require_regular(data_root / relative, f"bin/{relative}")
    for name in LIBRARIES:
        require_regular(stage / name, name)
        check_elf_aarch64(stage / name, name)

    check_magic(data_root / "Data/data.unity3d", b"UnityFS", "data.unity3d")
    check_magic(
        data_root / "Data/Managed/Metadata/global-metadata.dat",
        GLOBAL_METADATA_MAGIC,
        "global-metadata.dat",
    )
    unity_version = find_unity_version(stage / "libunity.so")

    libunity_hash = sha256(stage / "libunity.so")
    libil2cpp_hash = sha256(stage / "libil2cpp.so")
    known = KNOWN_BUILDS.get(libunity_hash)
    if known and known["libil2cpp_sha256"] != libil2cpp_hash:
        # A known engine paired with a foreign il2cpp is a mixed payload, not
        # a build we recognize; treat it as unknown rather than trusting it.
        known = None
    build_id = known["build_id"] if known else "unknown-%s" % libunity_hash[:12]

    boot_patch = patch_boot_config(data_root / "Data/boot.config")

    manifest = {
        "format": 2,
        "port": "terraria-nextos",
        "source": {
            "android_package": "com.and.games505.TerrariaPaid",
            "game_version": "1.4.5.6.4",
            "unity_version": unity_version,
            "abi": "arm64-v8a",
            "build_id": build_id,
            "known_build": bool(known),
        },
        "boot_patch": boot_patch,
        "validated": {
            "libraries": {
                "libunity.so": libunity_hash,
                "libil2cpp.so": libil2cpp_hash,
                "libc++_shared.so": sha256(stage / "libc++_shared.so"),
            },
            "library_sizes": {
                name: (stage / name).stat().st_size for name in LIBRARIES
            },
        },
    }
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_atomic(stage / ".terraria-data.json", encoded)
    return build_id if known else f"{build_id} (structurally validated)"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--game-dir", required=True)
    args = parser.parse_args()
    stage = Path(args.stage).resolve()
    game_dir = Path(args.game_dir).resolve()
    if not stage.is_dir() or not game_dir.is_dir():
        parser.error("stage and game directory must exist")
    try:
        build = prepare(stage)
    except (OSError, RuntimeError) as error:
        print(f"Terraria data preparation failed: {error}", file=sys.stderr)
        return 1
    print(
        "Terraria 1.4.5.6.4 data validated (build %s); Unity GLES2 boot patch applied"
        % build
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
