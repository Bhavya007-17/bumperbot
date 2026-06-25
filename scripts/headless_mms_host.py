#!/usr/bin/env python3
"""Minimal mms protocol host for automated runs without the GUI.

Pipe with the brain (host reads brain commands on stdin, writes responses on stdout):

    python3 scripts/headless_mms_host.py | python3 -m micromouse.gazebo_sync_brain

The brain uses full maze knowledge from maze_spec.json, so wall queries always
return false and motion always succeeds.
"""
import json
import os
import sys

SPEC = os.environ.get("MICROMOUSE_SPEC",
                     os.path.expanduser("~/.micromouse/maze_spec.json"))


def _size():
    try:
        with open(SPEC) as f:
            data = json.load(f)
        return int(data["n"])
    except Exception:
        return 16


def main():
    n = _size()
    for line in sys.stdin:
        parts = line.strip().split()
        if not parts:
            continue
        cmd = parts[0]
        if cmd == "mazeWidth":
            print(n)
        elif cmd == "mazeHeight":
            print(n)
        elif cmd in ("wallFront", "wallLeft", "wallRight"):
            print("false")
        elif cmd in ("moveForward", "turnLeft", "turnRight"):
            print("ack")
        elif cmd == "wasReset":
            print("false")
        elif cmd == "ackReset":
            print("ack")
        elif cmd in (
            "setColor", "clearColor", "clearAllColor",
            "setText", "clearText", "clearAllText",
            "setWall", "clearWall",
        ):
            continue
        else:
            print("ack", file=sys.stderr)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
