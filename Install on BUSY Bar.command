#!/bin/zsh
cd -- "${0:A:h}"
if command -v python3 >/dev/null 2>&1; then
  python3 -u install.py --launch
else
  print "Please install Python 3, then run this installer again."
fi
print "Press Return to close."
read
