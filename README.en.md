# Terraria — universal Android-version loader for NextOS / R36S

[Português (Brasil)](README.md) · [English](README.en.md)

![Terraria running in real 640x480 gameplay](docs/images/terraria-gameplay.png)

This project runs **Terraria Android 1.4.5.6.4**, Unity 2021.3.56f2 IL2CPP,
on AArch64 Linux handhelds through a native compatibility loader. It is the
Android-version loader: **not the FNA port**, not streaming, and it does not
include the game.

The public package is BYO-data: each user supplies their own legal APK. On the
first launch, NXExtract 1.2.0 identifies the exact release, verifies its ABI,
sizes and hashes, extracts only the required files, and applies the GLES2
configuration transactionally.

## Download

- [Release v1.0.2](https://github.com/NextOs-Ports/terraria-nextos/releases/tag/v1.0.2)
- [Download `terraria.zip`](https://github.com/NextOs-Ports/terraria-nextos/releases/download/v1.0.2/terraria.zip)
- SHA-256: `ff21f803f0fbee4ee30bc17ac1a93746abfab1027e04ff6b00d43c2738d6294e`

## Community

Questions, bug reports, help getting the port running, and news about the next ones:

💬 **Discord:** [discord.gg/DHfY62eDNN](https://discord.gg/DHfY62eDNN)

## Gallery — real on-device captures

| Gamepad-driven themed keyboard | Name committed through the original flow |
|---|---|
| ![Terraria QWERTY keyboard](docs/images/terraria-keyboard.png) | ![Codex name applied during creation](docs/images/terraria-name-confirmed.png) |

| Player created and saved | World generation |
|---|---|
| ![Player selection showing the created player](docs/images/terraria-player-created.png) | ![World generation reaching final cleanup](docs/images/terraria-world-generation.png) |

| Saved world ready to select | Gameplay |
|---|---|
| ![World selection screen](docs/images/terraria-world-select.png) | ![Terraria running on the handheld](docs/images/terraria-gameplay.png) |

Every image above is a 640x480 capture from physical-device validation. None
is a mockup.

## Compatibility status

| Item | Status |
|---|---|
| Architecture | AArch64 / ARM64 Linux |
| Supported game | Android `1.4.5.6.4`, package `com.and.games505.TerrariaPaid` |
| Engine | Unity `2021.3.56f2`, IL2CPP |
| Rendering | GLES2; SDL/KMSDRM or vendor EGL according to the backend that actually initialized |
| Public loader | one AArch64 ELF, maximum requirement `GLIBC_2.27` |
| NXExtract UI | maximum requirement `GLIBC_2.17` |
| Input | native Xbox/InControl controller + gamepad-driven name keyboard |
| Data | owner-supplied APK and game content; never bundled |

Physical validation is complete on an R36S-class handheld running ArkOS with
Mali-G31/KMSDRM and a 640x480 screen: boot, audio, controller, keyboard, player
naming, original creation flow, persistent save, world generation, gameplay,
and return to the frontend.

The NextOS Mali-450/fbdev family retains the vendor-EGL path already used by
the loader, and every packaged Linux ELF passes the low-glibc gate. Other
firmware and display combinations use the same capability-based selection but
still require physical testing; this project does not infer compatibility from
a successful build alone.

## Quick installation

1. Extract `terraria.zip` into the ports directory. `Terraria.sh` must sit next
   to the `terraria/` directory.
2. Put your legal Terraria Android **1.4.5.6.4** APK in
   `terraria/gamedata/`. Its filename does not matter.
3. Open `Terraria` in the frontend. NXExtract validates and prepares the data
   on the first launch.
4. To exit, use `Quit Game` inside Terraria or press `SELECT+START` together
   for an immediate exit.

The firmware must provide Python 3, SDL2, EGL and GLES2. See
[INSTALLATION.md](INSTALLATION.md) for installation, update, free-space, and
diagnostic details in both languages.

Expected layout after extracting the ZIP:

```text
ports/
├── Terraria.sh
└── terraria/
    ├── terraria
    ├── run.sh
    ├── extractor.json
    ├── nxextract.py
    └── gamedata/
        └── your-legal-1.4.5.6.4.apk
```

## Controls

Terraria receives an Xbox-style controller through its native InControl flow.
Menus, inventory, gameplay, glyphs, and remapping remain game-owned.

On the name keyboard:

| Action | Button |
|---|---|
| Navigate | D-pad |
| Activate key | `A` or `R3` |
| Delete | `B` |
| Toggle upper/lower case | `X` |
| Confirm with `DONE` | `START` |
| Cancel | `SELECT` |
| Exit immediately | `SELECT+START` together |

`SPACE`, `SHIFT`, `DEL`, and `DONE` are also directly selectable. The exit
shortcut works even while the keyboard is open. Terraria's own `Quit Game`
action also stops the loader and returns to the frontend.

## How the loader avoids depending on one device

- There is no fixed `/storage/roms/terraria` path.
- There are no device-name checks or `/dev/dri/card0` assumptions.
- The launcher does not force `SDL_VIDEODRIVER` or `SDL_AUDIODRIVER`.
- The backend SDL actually initializes decides context ownership:
  `mali`/fbdev uses vendor EGL; KMSDRM, Wayland, and other valid SDL backends
  use SDL-owned contexts and presentation.
- Resolution comes from a launcher override, then SDL's desktop mode, with a
  safe 640x480 fallback.
- SDL2 uses the firmware's stable ABI; SDL3 is neither required nor bundled.
- Presentation, controls, fixes, and frame lifecycle share the same pre-swap
  path instead of keeping device-specific fixes.
- The process stays in the foreground; the package does not use `setsid`,
  `nohup`, or frontend-service manipulation.

## Preserved native flow

The loader respects the game's Android/Unity sequence: JNI initialization,
graphics recreation, resume, focus, render loop, focus loss, and pause. It
intercepts compatibility; it does not invoke game stages out of order.

The overlay only replaces Android's unavailable software keyboard. Terraria
still runs `EnterName`, opens its editor, receives committed text on the next
managed-thread `Draw`, calls `CloseNameEdit`, and later follows the original
Create-button path. This applies to both player and world names, preserving
validation and save creation.

`Quit Game` preserves the original `SaveSettings` and social-shutdown flow, but
connects the Android version's empty `Game.Exit` method to the loader teardown.
The `false` return from `nativeRender` is honored as well. When `SELECT+START`
is pressed, the combo is consumed before it reaches the pause menu. All paths
converge on focus loss, `nativePause`, and a three-second watchdog that
guarantees return if a driver stalls on the final frame.

## Owner-supplied data

Accepted source:

- Android package: `com.and.games505.TerrariaPaid`;
- game version: `1.4.5.6.4`;
- Unity: `2021.3.56f2`, IL2CPP;
- ABI: `arm64-v8a`.

The recipe rejects a different release even if its file is renamed. The APK,
`libunity.so`, `libil2cpp.so`, `libc++_shared.so`, Unity data, saves, and
runtime logs are excluded from Git and from the public ZIP.

## NXExtract 1.2.0

The complete pinned NXExtract source is in `third_party/NXExtract/`, sourced
from the multi-device framework at commit
`400f87fb2aa4807d817403e23eb6965e3dd308e9`. It runs inside an isolated
firmware-library environment so extracted Android libraries cannot contaminate
Python or the setup UI.

Pinned runtime hashes:

- `nxextract.py`: `55664066d2ff0e5b7b83b6285d6606cca74923e80183d2f2e176e6353b93abd5`
- `nxextract-runtime-env.sh`: `332919a9960d4317563b647f9932d1a4367da147a425fe2f78eafd706f01563f`
- `run-extractor.sh`: `3c61f638a25f0ca9c5c5a94d33660886aaff17a18347c9e954afd4b0e9b3efba`
- `nxextract-ui`: `046afb583f5a211c946495e639409f81d9cfec706788eeccb7924b0e8e5a50b6`

## Build and package

The build host needs Docker, Bash, Python 3, `readelf`, ZIP tools, and the
current NextOS Amlogic-old sysroot for SDL/EGL/GLES headers.

```sh
./build_universal.sh
./package/build-package.sh
```

The first script builds inside Debian Buster and checks the glibc ceiling and
bionic TLS-guard layout. The second audits every ELF in the staging tree plus
scripts, metadata, and recipe; it rejects proprietary or diagnostic content
and produces a deterministic ZIP with a SHA-256 file.

After installing owner data with NXExtract, run the source tree with:

```sh
./Terraria.sh
```

## Source map

- `src/`: ELF loader, bionic/JNI/pthread/OpenSL/EGL compatibility, and
  Terraria hooks.
- `run.sh`: firmware-neutral foreground runtime.
- `package/r36s/Terraria.sh`: PortMaster entry point and BYO-data gate.
- `package/universal/extractor.json`: content-addressed extraction recipe.
- `tools/prepare_terraria_data.py`: validation and controlled `boot.config`
  patch.
- `third_party/NXExtract/`: complete NXExtract 1.2.0 source/runtime.
- `package/build-package.sh`: deterministic packaging and compatibility audit.

## Working references

- [Horizon Chase NextOS](https://github.com/NextOs-Ports/horizonchase-nextos):
  the validated multi-firmware SDL/EGL ownership and bionic signal strategy.
- [Prizefighters 2 NextOS](https://github.com/NextOs-Ports/prizefighters2-nextos):
  the validated pthread bridge and controller-keyboard design. Terraria uses
  its own palette and game-specific name-editor integration.

## Licenses and independence

The loader source is distributed under GNU GPL v3. Compatibility components
retain their notices in [NOTICE.md](NOTICE.md) and `licenses/`. NXExtract is
MIT licensed.

Terraria and all game content are proprietary works of their respective
rightsholders. This independent interoperability project is not affiliated
with or endorsed by Re-Logic, 505 Games, or Unity Technologies.
