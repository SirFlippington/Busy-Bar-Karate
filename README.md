# Karate for BUSY Bar

An endless arcade fighter for the front colour LED display. Defend against pink grabbers, strong orange guards and fast violet strikers. Every 100 points raises the level; every tenth level brings a leaping green miniboss. Defeat the boss to refill your health.

## Controls

- Setup: rotate the dial to choose Easy, Normal, Hard or INSANE; Start/Pause begins.
- Tap Start/Pause to punch; double-tap quickly to kick.
- Rotate clockwise to face right, counterclockwise to face left; press the dial to turn around.
- Back exits. At game over, Start/Pause retries and the dial button returns to setup.

Separate high scores are saved for each difficulty. No account or internet is required to play.

## Version 1.5.2

Original kung-fu-film-inspired 180 BPM chiptune music with plucked tones, gongs and percussion, separate punch/kick sounds, weightier impacts and bitcrushed synthesized martial-arts yells. Distinct character silhouettes and planted-body attack animations. Completely original pixel characters, moonlit rooftop background, music and effects replace all previously supplied third-party media. Gameplay and controls remain the same. Includes the setup-menu compatibility fix contributed by @mrlunev.

## Build and install

With Node.js 20+ and npm:

```sh
npm ci
npm test
npx busy-cli build
npx busy-cli app install
npx busy-cli app run
```

On macOS, use `COPYFILE_DISABLE=1 npx busy-cli build` to exclude macOS metadata. The app manifest targets API 27.12.0 or later. See DEVELOPING.md for details.

## Licence and assets

Code, documentation and all current media are MIT licensed. See ASSETS.md and generate_assets.py for the complete reproducible asset source.
