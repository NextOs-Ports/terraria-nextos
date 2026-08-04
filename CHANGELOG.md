# Changelog

## 1.0.3

- A fully installed game is no longer reported as a failed data setup.
  NXExtract 1.2.1 drops its scratch source cache only after every source
  archive is closed, and a removal the filesystem still refuses is logged
  instead of aborting the run. On FUSE-backed shares -- exFAT as Knulli and
  Batocera use it for `/userdata`, plus NFS and SMB -- a file unlinked while
  still open leaves a hidden placeholder behind, so `source-cache/bundle-*`
  answered `[Errno 39] Directory not empty` seconds after the payload had been
  committed and validated, and the launcher stopped with a data-setup error
  even though the extraction had finished correctly.
- The loader binary is unchanged from 1.0.2. This release touches the data
  extractor only.

## 1.0.2

- Connected Terraria's four-byte no-op `Game.Exit` method to the loader's
  guarded teardown, after the game's original settings-save and social
  shutdown steps have run.
- Honored the engine-owned `false` return from `nativeRender` as a second
  native Unity exit path instead of calling one more frame.
- Kept the already-validated immediate `SELECT+START` exit path unchanged.
- Added self-contained bilingual package documentation that does not depend on
  repository-only images or a release ZIP's own hash.

## 1.0.1

- Made `SELECT+START` exit immediately instead of requiring a 750 ms hold.
- Accepted firmware mappings that expose Select as either Back or Guide, with
  a device-scoped raw fallback for the GO-Super controller.
- Added a three-second process watchdog while preserving Terraria's native
  focus-loss and pause callbacks on the normal exit path.

## 1.0.0

- Rebuilt the Android Unity/IL2CPP loader as one public AArch64 binary requiring
  at most GLIBC_2.27.
- Removed firmware-specific absolute game paths and `/dev/dri` device guesses.
- Added capability-based SDL/raw-EGL ownership and real drawable sizing.
- Unified controller and Terraria frame hooks across both presentation paths.
- Added a Terraria-themed QWERTY controller keyboard with row-aware horizontal
  navigation and reliable `DONE` handling on the managed game thread.
- Preserved Terraria's original `EnterName` -> `CloseNameEdit` -> Create flow
  for player and world naming instead of invoking creation out of order.
- Added lifecycle-aware hotkey, SDL quit and signal shutdown.
- Added deterministic BYO-data installation for Android 1.4.5.6.4 with
  NXExtract 1.2.0.
- Added complete source, license notices, deterministic packaging and release
  gates for all included ELFs.
