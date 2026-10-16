# Busy-Bar-Karate<img width="1024" height="1536" alt="BUSY Bar - Karate" src="https://github.com/user-attachments/assets/bb850278-3822-4262-b6c9-55692944f9d0" />

I made a little game for BUSY Bar: Karate!

It’s an endless arcade fighter that runs entirely on the front colour LED screen. Enemies rush you from both sides, the difficulty increases every 100 points, and minibosses.

Controls
• Tap Start/Pause to punch.
• Double-tap it quickly to kick.
• Rotate the dial clockwise to face right or counterclockwise to face left; press inward to turn around.
• Press Back to exit.
• At game over, tap Start/Pause to try again.

Pink enemies grab, orange enemies are tougher, and black enemies attack quickly. Defeat a boss to refill your health! Your high score saves automatically.

To try it: download the attached ZIP, extract it, and follow the README. It includes Mac and Windows installers. You’ll need BUSY Bar firmware with native JavaScript app support - tested on dev firmware r1009.

## Download and source code

Download [Karate-BUSY-Bar-v1.4.0.zip from the v1.4.0 release](https://github.com/SirFlippington/Busy-Bar-Karate/releases/tag/v1.4.0) to install the game. The installer requires Python 3.

The game source is now available directly in [main.js](main.js), with its [app manifest](manifest.json), [installer](install.py), [build script](build.py) and [tests](test-game.cjs).

See [DEVELOPING.md](DEVELOPING.md) for instructions to edit, test, rebuild and install your own version. The build script combines the checked-out source with the media assets from the published release.

## Version 1.4.0: difficulty setup and dial controls

On opening Karate, select EASY, NORMAL, HARD or INSANE by rotating the dial (pressing it cycles forward). Press Start/Pause to begin READY → GO. The last difficulty is remembered. Normal preserves the original balance and high score; other modes save separate best scores. Easy reduces enemy pressure; Hard and INSANE increase spawn frequency, movement tiers and boss health.

During combat, rotate clockwise to face right, counterclockwise to face left, or press the dial to reverse. Single-tap Start/Pause punches; double-tap kicks. At game over, Start/Pause retries the same mode and pressing the dial returns to setup. Back exits.

Requires compatible native-app firmware; the manifest targets API 27.12.0 (r1018). This update was tested locally without a connected BUSY Bar.
