#!/usr/bin/env python3
"""Validate owned Terraria 1.4.5.6.4 data and apply the Unity boot patch."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


SOURCE_FILES = {
    "Data/Managed/Metadata/global-metadata.dat": (8805208, "7680b730578ba1d17bc8fd4097fe194c78d396181afbb737a236537f8eaea0a1"),
    "Data/Managed/Resources/Newtonsoft.Json.dll-resources.dat": (639, "10543fb9f9c7267c4f315bccabbd6a8d7482ce165b02d7b910fa4b733de61cfd"),
    "Data/Managed/Resources/mscorlib.dll-resources.dat": (337563, "c5baa176a5b72cd545266340e42102d393a5e43d38c95796bc828918bb95277f"),
    "Data/RuntimeInitializeOnLoads.json": (186, "8976eb231b5256bc8356e8e3ec58594c24849ac43feae616939dddbd5b7b6f03"),
    "Data/ScriptingAssemblies.json": (2623, "0dac1b6114fc009d12a43454ed2e4341c5384da9fc874073cef0f869e7445dba"),
    "Data/boot.config": (107, "f5c65ba0b2bec77444bfabe8bafdb87281283247c976eaf1b4fe2553cfbe5e3b"),
    "Data/data.unity3d": (70136966, "edd9116404ead3f690c465d78aa2a6b95df7a7d41e9222a9d8aa7c284c269fa1"),
    "Data/resources.resource": (81438912, "763bc43daf0589ef153088096b3e0329fba23e0766ac28dcb319bf0630c62c18"),
    "Data/unity default resources": (4222168, "05f10fe5e4ad3045d922265640ee1fcf7bf4bbf509c26b4d394eff7ec07690a1"),
    "Data/unity_app_guid": (36, "ad51696eb6acc4d11f885087719964e2c6d25da1e38a487e1173471beb857dff"),
}

LIBRARIES = {
    "libc++_shared.so": (1058904, "218ecc677aa79e1974f3968d2e0ecd0172c4f517188d04ebd7d45cbb285b5d03"),
    "libil2cpp.so": (54061072, "dc67ce5f48dc4738977e52fa524115beb95a641410eec39458adaf8f03b10c25"),
    "libunity.so": (13154416, "6456fbddbe10addc6c7c2253f8ad6ff589a01309945d1e1194d2890a21709574"),
}

BOOT_APPEND = (
    b"androidUseSwappy=0\n"
    b"gfx-disable-mt-rendering=1\n"
    b"gfx-enable-gfx-jobs=0\n"
    b"gfx-enable-native-gfx-jobs=0\n"
)
PATCHED_BOOT_SHA256 = "382f504549327ce2cdc94a37bbe2592ccb15a11d787ee911a5353f7e5e464dea"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(path: Path, size: int, expected_hash: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"missing regular file: {path.name}")
    actual_size = path.stat().st_size
    if actual_size != size:
        raise RuntimeError(f"unexpected size for {path.name}: {actual_size}")
    actual_hash = sha256(path)
    if actual_hash != expected_hash:
        raise RuntimeError(f"unexpected SHA-256 for {path.name}: {actual_hash}")


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


def prepare(stage: Path) -> None:
    data_root = stage / "bin"
    for relative, (size, expected_hash) in SOURCE_FILES.items():
        verify(data_root / relative, size, expected_hash)
    for relative, (size, expected_hash) in LIBRARIES.items():
        verify(stage / relative, size, expected_hash)

    boot_path = data_root / "Data/boot.config"
    source_boot = boot_path.read_bytes()
    patched_boot = source_boot + (b"" if source_boot.endswith(b"\n") else b"\n") + BOOT_APPEND
    if hashlib.sha256(patched_boot).hexdigest() != PATCHED_BOOT_SHA256:
        raise RuntimeError("internal boot.config patch checksum mismatch")
    write_atomic(boot_path, patched_boot, boot_path.stat().st_mode & 0o777)

    manifest = {
        "format": 1,
        "port": "terraria-nextos",
        "source": {
            "android_package": "com.and.games505.TerrariaPaid",
            "game_version": "1.4.5.6.4",
            "unity_version": "2021.3.56f2",
            "abi": "arm64-v8a",
        },
        "boot_patch": {
            "source_sha256": SOURCE_FILES["Data/boot.config"][1],
            "patched_sha256": PATCHED_BOOT_SHA256,
            "lines": BOOT_APPEND.decode("ascii").splitlines(),
        },
        "validated": {
            "bin_files": len(SOURCE_FILES),
            "bin_source_bytes": sum(item[0] for item in SOURCE_FILES.values()),
            "libraries": {name: value[1] for name, value in sorted(LIBRARIES.items())},
        },
    }
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_atomic(stage / ".terraria-data.json", encoded)


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
        prepare(stage)
    except (OSError, RuntimeError) as error:
        print(f"Terraria data preparation failed: {error}", file=sys.stderr)
        return 1
    print("Terraria 1.4.5.6.4 data validated; Unity GLES2 boot patch applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
