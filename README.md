# bumperbot

A ROS 2 mobile-robot workspace covering robot description, simulation, controllers, and example nodes — built while working through self-driving / ROS 2 fundamentals (odometry, control, and the publisher/subscriber/parameter patterns).

![ROS 2](https://img.shields.io/badge/ROS-2-22314E?logo=ros)
![Language](https://img.shields.io/badge/language-Python%20%2F%20C%2B%2B-3776AB?logo=python)
![Simulation](https://img.shields.io/badge/sim-Gazebo%20%2B%20RViz-orange)
![Status](https://img.shields.io/badge/status-learning%2Fin%20development-yellow)

## Overview

`bumperbot` is a ROS 2 workspace for a small differential-drive robot. It contains the robot's URDF/Xacro description and meshes, launch files for visualizing the robot in RViz and spawning it in Gazebo, a controller configuration, and a set of minimal example nodes that demonstrate core ROS 2 concepts. It's a hands-on learning project for ROS 2 robot bring-up and control, structured as a standard colcon workspace under `src/`.

> Note: this workspace follows the "Bumperbot" reference robot used in self-driving / ROS 2 coursework, re-implemented and extended here for learning.

## Packages

| Package | Language | What it contains |
|---------|----------|------------------|
| `bumperbot_description` | — | URDF/Xacro robot model, STL meshes, Gazebo and `ros2_control` xacros, RViz config, and `display.launch.py` / `gazebo.launch.py`. |
| `bumperbot_py_examples` | Python | Minimal `rclpy` nodes: `simple_publisher`, `simple_subscriber`, `simple_parameter`. |
| `bumperbot_controller` | Python | Controller configuration (`bumperbot_controllers.yaml`) and controller package scaffolding. |
| `bumperbot_cpp_examples` | C++ | C++ example package scaffold (CMake/ament). TODO: add example nodes. |

## Tech stack

- **Framework:** ROS 2 (ament / colcon)
- **Languages:** Python (`rclpy`) and C++ (`rclcpp`)
- **Simulation & viz:** Gazebo (`ros_gz_sim`, `ros_gz_bridge`), RViz2
- **Robot model:** URDF / Xacro, `robot_state_publisher`, `joint_state_publisher_gui`

## Getting started

### Prerequisites

- A ROS 2 installation (TODO: confirm the exact distro you target, e.g. Humble / Jazzy)
- `colcon`, plus the dependencies declared in each `package.xml` (Gazebo / `ros_gz`, `xacro`, `robot_state_publisher`, etc.)

### Build

```bash
# from the repo root (this directory is a colcon workspace)
colcon build
source install/setup.bash
```

### Run

```bash
# Visualize the robot model in RViz
ros2 launch bumperbot_description display.launch.py

# Spawn the robot in Gazebo
ros2 launch bumperbot_description gazebo.launch.py

# Run an example node
ros2 run bumperbot_py_examples simple_publisher
```

## Status

In development / learning workspace. Description, simulation launch, example nodes, and controller config are present; some packages (`bumperbot_cpp_examples`, parts of `bumperbot_controller`) are scaffolds.

## Roadmap

- TODO: confirm and document the target ROS 2 distro
- TODO: flesh out `bumperbot_controller` (diff-drive controller bring-up)
- TODO: add C++ example nodes to `bumperbot_cpp_examples`
- TODO: add odometry + teleop demo and a short screen recording

## Housekeeping

- This repo currently contains accidental Windows `*:Zone.Identifier` metadata files and large STL meshes. A `.gitignore` has been added to prevent new ones; see the repo maintainer's notes about removing the existing tracked copies.

## License

The `bumperbot_description` and `bumperbot_py_examples` packages declare **Apache-2.0** in their `package.xml`. TODO: add a top-level `LICENSE` file and set licenses for the remaining packages.

## Contact

Bhavya Dosi — [LinkedIn](https://www.linkedin.com/in/bhavya-dosi)
