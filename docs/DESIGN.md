# Design — Micromouse ROS 2 stack

## Problem statement

Build a micromouse solver that:

1. Reproduces the mms flood-fill screenshot (distance in every cell, blue trail to center).
2. Mirrors every mms cell move on a Gazebo robot **in lockstep** (same command stream).
3. Runs fast enough to iterate on WSL without a discrete GPU.

## Solution overview

Three artifacts share one maze definition:

| File | Consumer |
|------|----------|
| `maze.num` | mms GUI |
| `maze_spec.json` | Brain + motion controller |
| `maze.world` | Gazebo Harmonic |

The brain (`gazebo_sync_brain.py`) is launched by mms as a subprocess. Its **stdout** is the mms command channel; diagnostics go to **stderr** only.

## Protocol bridge

The brain publishes ROS commands in parallel with mms animation:

```
mms.move_forward()  ─┬─► mms GUI animates the virtual mouse
                     └─► bridge.send("moveForward") → /maze/mms_command
```

The controller acknowledges each finished move on `/maze/step_complete`. The brain waits only at the **end** so mms keeps the process alive until Gazebo drains the queue.

## Motion controller

`cell_motion_controller` uses Gazebo `/world/<name>/set_pose` instead of velocity control:

- **Exact cells** — no integrator drift or overshoot.
- **WSL-friendly** — avoids the slow `ros_gz_bridge` cmd_vel path.
- **FIFO worker** — subscription callback only enqueues; a thread animates one command at a time.

Commands: `moveForward`, `turnLeft`, `turnRight`, `resetToStart`.

## Visualization

`brain_viz` is a lightweight pygame window subscribed to `/maze/current_cell`. It does not render 3D; it shows the same distance field the brain computed, plus the live trail.

## Recording pipeline

`scripts/record_full_session.sh`:

1. Kills stale Gazebo/controller processes.
2. Regenerates maze with `--top-down-cam` for square overhead Gazebo view.
3. Launches simulation, runs `headless_mms_host.py | gazebo_sync_brain.py`.
4. `record_session_gifs.py` samples `/maze/current_cell` into brain + overhead GIFs.
5. `render_solve_gif.py` produces the offline mms animation for the README.

## Failure modes

| Symptom | Likely cause |
|---------|----------------|
| Robot stuck mid-maze | Second `ros2 launch` still running — kill with pkill one-liner |
| mms "No such file" for brain | Run command must use `run_brain.sh` (sources ROS + workspace) |
| Robot not at start on Run | Missing `resetToStart` or duplicate controllers fighting set_pose |
| Maze/spec mismatch crash | Regenerate maze; reload `.num` in mms |
