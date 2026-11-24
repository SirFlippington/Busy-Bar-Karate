# Building Karate

Requires Node.js 20 or later and npm.

```sh
npm ci
npm test
npx busy-cli build
npx busy-cli app install
npx busy-cli app run
```

On macOS, use `COPYFILE_DISABLE=1 npx busy-cli build` to prevent macOS metadata sidecars entering the package. The catalog builds on Linux and needs no special setting.

The pinned official CLI and lockfile allow offline builds after dependencies are installed. All required images, animations and audio are committed; building does not download media or run custom scripts.

The runtime entry is main.js and the package manifest is appmeta/manifest.json. The root manifest.json is retained for the older Python packaging workflow and must match the appmeta copy.

The screenshots were captured from the official BUSY Bar Emulator using firmware 1.4.1 (API 27.15.0). Tests cover setup visibility, difficulty, controls, combat, bosses, scoring and music transitions.
