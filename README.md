# Terraria — universal Android Unity loader for NextOS / R36S

## Visão geral (PT-BR)

Este projeto executa **Terraria Android 1.4.5.6.4**, Unity 2021.3.56f2
IL2CPP, em aparelhos Linux AArch64 por meio de um loader de compatibilidade
nativo. É o loader da versão Android: **não é o port FNA** e não contém o jogo.

O ZIP público é BYO-data. Na primeira execução, NXExtract 1.2.0 localiza o APK
legal fornecido pelo usuário, confere conteúdo, ABI, tamanhos e hashes, aplica a
configuração GLES2 de forma transacional e só então libera o loader.

## Overview (EN)

This project runs **Terraria Android 1.4.5.6.4**, Unity 2021.3.56f2 IL2CPP,
on AArch64 Linux handhelds through a native compatibility loader. It is the
Android loader, **not the FNA port**, and it does not include the game.

The public ZIP is BYO-data. On first launch, NXExtract 1.2.0 finds the owner's
legal APK, verifies content, ABI, sizes and hashes, applies the GLES2 setup in a
transaction, and only then allows the loader to start.

## Compatibility architecture

- One AArch64 executable for the public package; maximum requirement
  `GLIBC_2.27` (release gate: no newer than `GLIBC_2.30`).
- The loader uses the firmware's stable SDL2 ABI; SDL3 is neither required nor
  bundled.
- The launcher never forces `SDL_VIDEODRIVER` or `SDL_AUDIODRIVER`.
- SDL's actual initialized video driver decides ownership:
  `mali`/fbdev-class backends retain the vendor EGL path; KMSDRM, Wayland and
  other successful SDL backends use SDL-owned GLES contexts and presentation.
- GLES2 is the default. Window size comes from the launcher override when
  present, then the SDL desktop mode, with a safe 640×480 fallback.
- Both presentation paths run the same Terraria hooks for native controller
  input, on-screen name entry, render fixes and frame lifecycle.
- `SELECT+START` requests focus loss and `nativePause` immediately. A three
  second process watchdog guarantees return to the frontend if a vendor driver
  stalls during the final frame.
- A foreground process model is used. No `setsid`, `nohup`, frontend service
  manipulation or background double-launch is part of the package.

## Problems solved

- Removed the former hard-coded `/storage/roms/terraria` layout from native
  asset, library, save, storage-space and diagnostic paths.
- Replaced device-name/`/dev/dri/card0` guesses with actual SDL capability
  detection and a single clean fallback attempt.
- Kept the Android lifecycle order: `initJni`, graphics recreation, resume,
  focus, render loop, focus loss and pause.
- Shared the before-present input/fix path between raw Mali/fbdev and SDL-owned
  presentation; the older SDL/KMS path skipped part of it.
- Preserved the validated InControl Xbox path, FMOD-to-SDL audio, player/world
  creation and persistent saves from the original working loader.
- Added a Terraria-themed QWERTY controller keyboard. Horizontal navigation is
  row-aware, and `DONE` publishes the text on the managed game thread before
  Terraria's original close/create flow consumes it.
- Compiled release diagnostics out of the public ELF and made verbose frame
  logs opt-in.

## Validated compatibility

| Profile | Result |
|---|---|
| R36S-class ArkOS, AArch64, KMSDRM/Mali-G31, 640x480 | Boot, audio, controller, keyboard navigation, player naming, original player creation, persistent save and gameplay validated |
| NextOS Mali-450/fbdev family | Preserves the already-working vendor EGL path; public binary and packaged UI pass the low-glibc gate |

The package deliberately avoids device-name checks. Other firmware and display
combinations use the same capability-based paths, but still require physical
testing; compatibility is not inferred from a successful build alone.

## Controls

Terraria receives an Xbox-style controller through its native InControl flow,
so menu, inventory, gameplay bindings and glyphs remain game-owned. The
on-screen name keyboard uses the D-pad to navigate, A or R3 to activate the
selected key, B to delete, X to change case, Start to activate `DONE`, and
Select to cancel. `SPACE`, `SHIFT`, `DEL` and `DONE` are also selectable keys.
Press `SELECT+START` together to exit, including while the keyboard is open.

Exact gameplay bindings can be changed in Terraria's own controller settings.

## Native keyboard flow

The overlay replaces only Android's unavailable software keyboard. It does not
jump to creation methods: Terraria still executes `EnterName`, opens its name
editor, receives the committed text through the next managed `Draw`, runs
`CloseNameEdit`, and later invokes its original Create button path. The same
rule is used for player and world names, keeping validation and save creation
inside the game's native order.

## Owner-supplied data

Supported source:

- Android package: `com.and.games505.TerrariaPaid`
- Game version: `1.4.5.6.4`
- Unity: `2021.3.56f2`, IL2CPP
- ABI: `arm64-v8a`

Place the legal APK in `terraria/gamedata/` and launch `Terraria.sh`. The APK
filename does not matter. The recipe rejects another release even if its name
looks correct. See [INSTALLATION.md](INSTALLATION.md).

The APK, `libunity.so`, `libil2cpp.so`, `libc++_shared.so`, Unity data, saves
and generated runtime logs are excluded from Git and from the public ZIP.

## NXExtract provenance

The standalone source tree vendors NXExtract `1.2.0` from the canonical
multi-device framework at commit `400f87fb2aa4807d817403e23eb6965e3dd308e9`.
Release audits pin these runtime hashes:

- `nxextract.py`: `55664066d2ff0e5b7b83b6285d6606cca74923e80183d2f2e176e6353b93abd5`
- `nxextract-runtime-env.sh`: `332919a9960d4317563b647f9932d1a4367da147a425fe2f78eafd706f01563f`
- `run-extractor.sh`: `3c61f638a25f0ca9c5c5a94d33660886aaff17a18347c9e954afd4b0e9b3efba`
- `nxextract-ui`: `046afb583f5a211c946495e639409f81d9cfec706788eeccb7924b0e8e5a50b6`

NXExtract runs in an isolated firmware-library environment so extracted
Android libraries cannot contaminate Python or the setup UI process.

## Build and package

Requirements on the build host: Docker, a current NextOS Amlogic-old sysroot
for SDL/EGL/GLES headers, Bash, `readelf`, Python 3 and ZIP tools.

```sh
./build_universal.sh
./package/build-package.sh
```

`build_universal.sh` compiles in Debian Buster and verifies the glibc ceiling
and the bionic TLS guard layout. `package/build-package.sh` then audits every
ELF in the staged release, checks scripts/metadata/recipe, rejects proprietary
or diagnostic content, and creates a deterministic ZIP plus SHA-256 file.

For a source-tree run after installing owner data with NXExtract:

```sh
./Terraria.sh
```

## Source map

- `src/`: ELF loader, bionic/JNI/pthread/OpenSL/EGL compatibility and Terraria
  controller/runtime hooks.
- `run.sh`: firmware-neutral foreground runtime.
- `package/r36s/Terraria.sh`: PortMaster entry point and BYO-data gate.
- `package/universal/extractor.json`: content-addressed extraction recipe.
- `tools/prepare_terraria_data.py`: exact data validation and boot.config patch.
- `third_party/NXExtract/`: complete pinned NXExtract 1.2.0 source/runtime.
- `package/build-package.sh`: deterministic release and compatibility audit.

## Working references

- [Horizon Chase NextOS](https://github.com/NextOs-Ports/horizonchase-nextos)
  provided the already-validated multi-firmware SDL/EGL ownership and bionic
  signal-set strategy.
- [Prizefighters 2 NextOS](https://github.com/NextOs-Ports/prizefighters2-nextos)
  provided the already-validated pthread bridge and controller-keyboard design;
  the Terraria overlay uses its own palette and Terraria-specific managed-name
  integration.

## Licenses and independence

The loader source is distributed under GNU GPL v3. Upstream compatibility
components retain their notices in [NOTICE.md](NOTICE.md) and `licenses/`.
NXExtract is MIT licensed.

Terraria and all game content are proprietary works of their respective
rightsholders. This independent interoperability project is not affiliated
with or endorsed by Re-Logic, 505 Games or Unity Technologies.
