#!/usr/bin/env python3
"""Bring up Gazebo with the generated maze, spawn the robot, start the
pose-driven cell-motion controller, and (optionally) the live brain window.

No ros_gz bridge is needed: the controller moves the robot via the Gazebo
set_pose service, and the brain/controller/viz talk over plain ROS topics. This
sidesteps the slow /cmd_vel bridge on WSL/no-GPU machines.

Run `ros2 run micromouse generate_maze` first.

Usage:
  ros2 launch micromouse maze_gazebo.launch.py
  ros2 launch micromouse maze_gazebo.launch.py headless:=true     # no gz GUI
  ros2 launch micromouse maze_gazebo.launch.py viz:=false
  ros2 launch micromouse maze_gazebo.launch.py spec:=/path/maze_spec.json \
                                               world:=/path/maze.world
"""
import json
import math
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            LogInfo, OpaqueFunction, TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

WHEEL_RADIUS = 0.04
WORLD_NAME = "micromouse"   # must match <world name=...> in the generated SDF
MODEL_NAME = "micromouse"   # the spawned robot's entity name


def _setup(context, *args, **kwargs):
    spec_path = LaunchConfiguration("spec").perform(context)
    world_path = LaunchConfiguration("world").perform(context)
    headless = LaunchConfiguration("headless").perform(context) == "true"

    if not os.path.exists(spec_path) or not os.path.exists(world_path):
        raise RuntimeError(
            "missing maze files. Run:  ros2 run micromouse generate_maze\n"
            "  spec : %s\n  world: %s" % (spec_path, world_path))

    with open(spec_path) as f:
        spec = json.load(f)
    cell = float(spec["cell_size_m"])
    sc = spec["start_cell"]
    sx = sc[0] * cell + cell / 2.0
    sy = sc[1] * cell + cell / 2.0
    yaw = math.pi / 2.0  # North (+y)

    pkg = get_package_share_directory("micromouse")
    xacro_file = os.path.join(pkg, "description", "micromouse.urdf.xacro")
    robot_description = os.popen("xacro " + xacro_file).read()

    ros_gz_sim = get_package_share_directory("ros_gz_sim")
    gz_args = ("-s -r -v3 " if headless else "-r -v3 ") + world_path
    gz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")),
        launch_arguments={"gz_args": gz_args}.items(),
    )

    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description}],
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=["-world", WORLD_NAME,
                   "-topic", "robot_description", "-name", MODEL_NAME,
                   "-x", str(sx), "-y", str(sy), "-z", str(WHEEL_RADIUS),
                   "-Y", str(yaw)],
    )
    # Let Gazebo finish loading the world before spawning the robot.
    delayed_spawn = TimerAction(period=5.0, actions=[spawn])

    steps_arg = int(LaunchConfiguration("steps").perform(context))
    step_dt_arg = float(LaunchConfiguration("step_dt").perform(context))
    controller = Node(
        package="micromouse",
        executable="cell_motion_controller",
        output="screen",
        parameters=[{"spec_path": spec_path,
                     "world_name": WORLD_NAME,
                     "model_name": MODEL_NAME,
                     "robot_z": WHEEL_RADIUS,
                     "steps": steps_arg,
                     "step_dt": step_dt_arg}],
    )

    viz = Node(
        package="micromouse",
        executable="brain_viz",
        output="screen",
        additional_env={"MICROMOUSE_SPEC": spec_path},
        condition=IfCondition(LaunchConfiguration("viz")),
    )

    solver = os.path.join(pkg, "..", "..", "lib", "micromouse",
                          "gazebo_sync_brain")
    steps = LogInfo(msg=(
        "\n" + "=" * 70 +
        "\nMaze + robot up. Configure the mms GUI:\n"
        "  Maze  -> " + os.path.join(os.path.dirname(spec_path), "maze.num") +
        "\n  Mouse -> Run command:  python3 " + solver +
        "\n  (or point it at micromouse/gazebo_sync_brain.py in your src tree)"
        "\nLaunch mms from a terminal that sourced ROS + this workspace.\n"
        + "=" * 70))

    return [gz, rsp, delayed_spawn, controller, viz, steps]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "spec", default_value=os.path.expanduser(
                "~/.micromouse/maze_spec.json")),
        DeclareLaunchArgument(
            "world", default_value=os.path.expanduser(
                "~/.micromouse/maze.world")),
        DeclareLaunchArgument("headless", default_value="false"),
        DeclareLaunchArgument("viz", default_value="true"),
        # Motion smoothness vs speed. steps:=1 = instant teleport (fastest);
        # raise both for a smoother glide.
        DeclareLaunchArgument("steps", default_value="2"),
        DeclareLaunchArgument("step_dt", default_value="0.01"),
        OpaqueFunction(function=_setup),
    ])
