# Changelog

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
