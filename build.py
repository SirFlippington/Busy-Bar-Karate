#!/usr/bin/env python3
"""Package the editable game source with the published v1.3.2 media assets.

Python standard library only. Does not install or launch anything on BUSY Bar.
"""
import argparse
import hashlib
import io
import shutil
import tarfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

APP = 'app.kungfu.endless'
ROOT = Path(__file__).resolve().parent
ASSET_URL = 'https://github.com/SirFlippington/Busy-Bar-Karate/releases/download/v1.3.2/Karate-BUSY-Bar.zip'
ASSET_SHA256 = 'ac9bfdc7814637dd6834896f9b3712c8d39b0aa9ada68e94951797def79eacf9'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-zip', type=Path, help='Use a downloaded v1.3.2 Karate-BUSY-Bar.zip instead of downloading it')
    args = parser.parse_args()
    destination = ROOT / 'build'
    destination.mkdir(exist_ok=True)
    archive = args.assets_zip or destination / 'assets-v1.3.2.zip'
    if not archive.exists():
        if args.assets_zip:
            parser.error('The supplied assets ZIP does not exist.')
        print('Downloading published game media...')
        with urllib.request.urlopen(ASSET_URL, timeout=180) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != ASSET_SHA256:
            raise RuntimeError('Published asset checksum mismatch; nothing extracted.')
        archive.write_bytes(data)
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != ASSET_SHA256:
        raise RuntimeError('Expected the original v1.3.2 release ZIP; checksum mismatch.')
    app_root = destination / APP
    with zipfile.ZipFile(io.BytesIO(data)) as release:
        packed = release.read('Karate/Karate.tgz')
    with tarfile.open(fileobj=io.BytesIO(packed), mode='r:gz') as assets:
        for member in assets.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts:
                raise RuntimeError('Unsafe asset path.')
            if len(path.parts) < 3 or path.parts[0] != APP:
                continue
            if path.parts[1] not in ('animations', 'images', 'sounds', 'appmeta'):
                continue
            if not member.isfile() or path.name == 'manifest.json':
                continue
            target = destination.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with assets.extractfile(member) as source, target.open('wb') as output:
                shutil.copyfileobj(source, output)
    (app_root / 'scripts').mkdir(parents=True, exist_ok=True)
    (app_root / 'appmeta').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / 'main.js', app_root / 'scripts/main.js')
    shutil.copyfile(ROOT / 'manifest.json', app_root / 'appmeta/manifest.json')
    with tarfile.open(destination / 'Karate.tgz', 'w:gz', format=tarfile.USTAR_FORMAT) as package:
        for path in sorted(app_root.rglob('*')):
            if path.is_file() and not path.name.startswith('.'):
                info = package.gettarinfo(str(path), str(path.relative_to(destination)))
                info.uid = info.gid = 0
                info.uname = info.gname = ''
                info.mode = 0o644
                with path.open('rb') as stream:
                    package.addfile(info, stream)
    files = ['install.py', 'Install on BUSY Bar.command', 'Install on Windows.cmd', 'README.md']
    for name in files:
        shutil.copyfile(ROOT / name, destination / name)
    (destination / 'Install on BUSY Bar.command').chmod(0o755)
    with zipfile.ZipFile(destination / 'Karate-BUSY-Bar.zip', 'w', zipfile.ZIP_DEFLATED) as bundle:
        for name in ['Karate.tgz'] + files:
            bundle.write(destination / name, 'Karate/' + name)
    print('Built:', destination / 'Karate-BUSY-Bar.zip')
    print('To install over USB: python3 build/install.py --launch')


if __name__ == '__main__':
    main()
