# Developing Karate

The editable source for the released game is in this repository:

- `main.js`: complete BUSY Bar JavaScript game, including controls, combat, bosses, display updates, audio scheduling and saved scores.
- `manifest.json`: native app identity, version and heap allocation.
- `install.py`: standard-library Python installer using BUSY Bar's local API.
- `build.py`: creates an installable package from the checked-out source and the published media assets.
- `test-game.cjs`: simulated-runtime checks for combat, controls, bosses, audio transitions and saved scores.

The `.anim`, `.snd` and image files are bundled in the existing v1.3.2 release. The build script reuses those assets; it does not regenerate the sprites or audio from their original recordings. No computer-specific paths or device credentials are needed.

## Build

Install Python 3, then run from this folder:

```sh
python3 build.py
```

The first run downloads the v1.3.2 release ZIP and checks its SHA-256 before extracting the media. To build offline using a copy you already downloaded:

```sh
python3 build.py --assets-zip /path/to/Karate-BUSY-Bar.zip
```

The output is `build/Karate-BUSY-Bar.zip`. It includes the checked-out `main.js` and `manifest.json`, packaged at the paths BUSY Bar expects. Edit the root source files and rebuild to make changes. Generated files under `build/` are ignored by Git.

## Check changes

With Node.js installed:

```sh
node --check main.js
node test-game.cjs
```

Tests run locally without contacting a device. When `build/app.kungfu.endless` exists, they also verify referenced assets. They cannot measure physical LED frame rate or audible playback; animation and audio changes still need testing on a BUSY Bar.

## Install your build

Connect BUSY Bar by USB, quit any running app, then run:

```sh
python3 build/install.py --check
python3 build/install.py --launch
```

The default USB address is `10.0.4.20`. The installer also supports `--host DEVICE_IP --wifi`, which prompts for the device API password without storing it. Firmware must support native JavaScript apps; the release was tested on dev firmware r1009.

Keep the app ID `app.kungfu.endless` to preserve existing Karate high scores across updates. The internal ID predates the rename to Karate.

## Runtime design

The game runs on BUSY Bar's JerryScript runtime. `listen('input', ...)` handles buttons. The game updates every 50 ms and sends only changed display elements through the local API. Native 30 fps animation files handle movement between those updates. Live animation sections loop to avoid the firmware's stopped-timer behaviour when switching sections; the player's death clip finishes on a transparent frame.

BUSY Bar exposes one audio playback channel. Combat effects are mixed with quiet music at different resume points. Intro, celebration and game-over cues use separate files. Game over plays its cue once and does not restart background music.
