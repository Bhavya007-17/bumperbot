#!/usr/bin/env bash
# mms "Run command" wrapper.
#
# mms launches the mouse algorithm with whatever environment mms itself had,
# which often does NOT include ROS (so `python3`/`rclpy` look "missing" and mms
# reports "No such file or directory"). This wrapper sources ROS + the workspace
# first, then execs the brain, so it works no matter how mms is started.
set -e

# Source ROS 2 (edit the distro here if you are not on Jazzy).
if [ -f /opt/ros/jazzy/setup.bash ]; then
  # shellcheck disable=SC1091
  source /opt/ros/jazzy/setup.bash
fi

# Source this workspace, resolved relative to THIS script's location.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_INSTALL="$SCRIPT_DIR/../../install/setup.bash"
if [ -f "$WS_INSTALL" ]; then
  # shellcheck disable=SC1091
  source "$WS_INSTALL"
fi

exec python3 "$SCRIPT_DIR/micromouse/gazebo_sync_brain.py"
