#!/usr/bin/env python3
"""Run gazebo_sync_brain with an in-process headless mms host (no FIFO deadlock)."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAIN = os.path.join(ROOT, "src", "micromouse", "micromouse", "gazebo_sync_brain.py")
SPEC = os.environ.get("MICROMOUSE_SPEC",
                       os.path.expanduser("~/.micromouse/maze_spec.json"))
LOG = os.path.join(ROOT, "logs", "brain.log")


def _size():
    with open(SPEC) as f:
        return int(json.load(f)["n"])


def _respond(cmd, n):
    if cmd == "mazeWidth":
        return str(n)
    if cmd == "mazeHeight":
        return str(n)
    if cmd in ("wallFront", "wallLeft", "wallRight"):
        return "false"
    if cmd in ("moveForward", "turnLeft", "turnRight", "ackReset"):
        return "ack"
    if cmd == "wasReset":
        return "false"
    return None


def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    n = _size()
    with open(LOG, "w") as err:
        proc = subprocess.Popen(
            [sys.executable, BRAIN],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=err,
            text=True,
            bufsize=1,
        )
        assert proc.stdin and proc.stdout
        for line in proc.stdout:
            parts = line.strip().split()
            if not parts:
                continue
            reply = _respond(parts[0], n)
            if reply is not None:
                proc.stdin.write(reply + "\n")
                proc.stdin.flush()
        proc.wait()
    return proc.returncode or 0


if __name__ == "__main__":
    sys.exit(main())
