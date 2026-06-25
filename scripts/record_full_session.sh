#!/usr/bin/env bash
# One-shot: clean up, generate maze, launch Gazebo, run brain, record GIFs.
#
# Usage (from repo root, in WSL with ROS Jazzy sourced):
#   ./scripts/record_full_session.sh
#   ./scripts/record_full_session.sh --seed 7
set -eo pipefail

SEED=42
while [[ $# -gt 0 ]]; do
  case "$1" in
    --seed) SEED="$2"; shift 2 ;;
    *) echo "unknown arg: $1"; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p media logs

# Source ROS + workspace.
if [[ -f /opt/ros/jazzy/setup.bash ]]; then
  # shellcheck disable=SC1091
  source /opt/ros/jazzy/setup.bash
fi
if [[ -f "$ROOT/install/setup.bash" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/install/setup.bash"
fi

export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/mnt/wslg/runtime-dir}"

echo "==> cleaning leftover processes"
pkill -9 -f cell_motion_controller 2>/dev/null || true
pkill -9 -f "gz sim" 2>/dev/null || true
pkill -9 -f brain_viz 2>/dev/null || true
pkill -9 -f gazebo_sync_brain 2>/dev/null || true
sleep 1

echo "==> generating maze (seed=$SEED, top-down camera)"
ros2 run micromouse generate_maze --seed "$SEED" --top-down-cam

echo "==> rendering offline mms solve GIF"
python3 scripts/render_solve_gif.py --seed "$SEED" \
  --gif media/mms_solve.gif --png media/mms_solved.png

echo "==> launching Gazebo + controller (background)"
ros2 launch micromouse maze_gazebo.launch.py steps:=2 step_dt:=0.01 \
  > logs/gazebo_launch.log 2>&1 &
LAUNCH_PID=$!

cleanup() {
  kill "$LAUNCH_PID" 2>/dev/null || true
  pkill -9 -f cell_motion_controller 2>/dev/null || true
  pkill -9 -f "gz sim" 2>/dev/null || true
  pkill -9 -f brain_viz 2>/dev/null || true
}
trap cleanup EXIT

echo "==> waiting 12s for robot at start cell"
sleep 12

echo "==> starting live GIF recorder"
python3 scripts/record_session_gifs.py --duration 45 --interval 0.15 \
  > logs/recorder.log 2>&1 &
REC_PID=$!
sleep 2

echo "==> running brain via automated mms host"
MICROMOUSE_STEP_TIMEOUT=90 python3 scripts/run_automated_brain.py || true

echo "==> waiting for recorder"
wait "$REC_PID" 2>/dev/null || true
sleep 2

echo "==> done. media/:"
ls -la media/*.gif media/*.png 2>/dev/null || true
