#!/usr/bin/env python3
"""Build the original-assets edition using the official BUSY CLI."""
import os, subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
env=dict(os.environ, COPYFILE_DISABLE="1")
subprocess.run(["npx", "--no-install", "busy-cli", "build"], cwd=root, env=env, check=True)
