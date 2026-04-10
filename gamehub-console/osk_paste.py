#!/usr/bin/env python3
import subprocess


def run():
    subprocess.run(
        ["xdotool", "key", "--clearmodifiers", "ctrl+v"],
        check=False,
    )
