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
4. `record_session_gifs.py` collects the full ordered trail, then renders brain + overhead GIFs.
5. `render_solve_gif.py` produces the offline mms animation for the README.

### Why the trail topic is `TRANSIENT_LOCAL`

The brain fires the whole 64-move path onto `/maze/current_cell` in a **sub-second
burst**. A freshly started recorder using the default `RELIABLE`+`VOLATILE` QoS
matches the brand-new publisher *after* the burst has already gone out, so every
message is dropped and the GIF is a single static start-cell frame.

Two changes make recording deterministic regardless of process start order:

- **`TRANSIENT_LOCAL` durability + deep history (1024)** on every `current_cell`
  publisher (brain and controller) and on the recorder's subscription. A late
  subscriber *replays* the entire buffered trail.
- The recorder **collects first, renders second**. Rendering is done offline
  (one frame per cell) so matplotlib never starves the rclpy executor, and the
  animation length is decoupled from how fast cells arrive over the wire.

The brain also waits for `pub.get_subscription_count() > 0` (command + cell
topics) before sending, closing the same first-message race on the command path.

## The Gazebo 3D viewport on WSL / GPU-less hosts

On WSL without a discrete GPU, the Gazebo Harmonic **GUI** logs:

```
Failed to load plugin [] : couldn't load library on path
  [/opt/ros/jazzy/opt/gz_rendering_vendor/lib/]
```

This is the Ogre 3D **render-engine** failing to initialise — it is a viewport
limitation, **not** a solver fault. The stack is intentionally **pose-driven**:
the physics server, `set_pose` service, motion controller, flood-fill brain, and
the synthetic overhead recorder all work without any 3D rendering. The robot
still traverses the maze; the demo GIFs are drawn from ROS topics, not from the
3D camera. If you need the 3D window, run on a host with OpenGL/GPU acceleration
or set `LIBGL_ALWAYS_SOFTWARE=1` for slow software rendering.

## Failure modes

| Symptom | Likely cause |
|---------|----------------|
| Robot stuck mid-maze | Second `ros2 launch` still running — kill with pkill one-liner |
| mms "No such file" for brain | Run command must use `run_brain.sh` (sources ROS + workspace) |
| Robot not at start on Run | Missing `resetToStart` or duplicate controllers fighting set_pose |
| Maze/spec mismatch crash | Regenerate maze; reload `.num` in mms |
| `robot did 0/N moves` / empty GIF | First-message QoS race — fixed by `TRANSIENT_LOCAL` trail + subscriber wait |
| Gazebo GUI `engine []` / blank 3D view | No GPU render engine on WSL — cosmetic; solve + GIFs are unaffected |
