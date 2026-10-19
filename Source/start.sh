#!/bin/bash
cd "$(dirname "$0")"

if [ -f "venv/bin/python" ]; then
    venv/bin/python start_all.py
else
    python3 start_all.py
fi
