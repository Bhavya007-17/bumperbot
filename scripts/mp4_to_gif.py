#!/usr/bin/env python3
"""Convert micromouse_demo.mp4 to an optimized GIF for GitHub README autoplay."""
import os
import sys

import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "media", "micromouse_demo.mp4")
DST = os.path.join(ROOT, "media", "micromouse_demo.gif")
MAX_WIDTH = 720
FRAME_STEP = 5      # ~6 fps from 30 fps source
MAX_FRAMES = 150
DURATION_MS = 167   # ~6 fps


def main():
    cap = cv2.VideoCapture(SRC)
    if not cap.isOpened():
        sys.exit("cannot open %s" % SRC)

    frames = []
    idx = 0
    while len(frames) < MAX_FRAMES:
        ret, bgr = cap.read()
        if not ret:
            break
        if idx % FRAME_STEP == 0:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            w, h = img.size
            if w > MAX_WIDTH:
                nh = int(h * MAX_WIDTH / w)
                img = img.resize((MAX_WIDTH, nh), Image.Resampling.LANCZOS)
            frames.append(img.convert("P", palette=Image.Palette.ADAPTIVE, colors=128))
        idx += 1
    cap.release()

    if not frames:
        sys.exit("no frames extracted")

    os.makedirs(os.path.dirname(DST), exist_ok=True)
    frames[0].save(
        DST,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION_MS,
        loop=0,
        optimize=True,
    )
    print("wrote %s (%d frames, %.1f MB)" % (
        DST, len(frames), os.path.getsize(DST) / 1_048_576))


if __name__ == "__main__":
    main()
