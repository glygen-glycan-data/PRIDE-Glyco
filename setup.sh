#!/bin/sh
set -x
if [ -d .venv ]; then
  rm -rf .venv
fi
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
