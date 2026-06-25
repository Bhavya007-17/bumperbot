#!/usr/bin/env python3
"""Cell-motion controller (POSE-DRIVEN, decoupled).

Drives the robot by commanding ABSOLUTE model poses through the Gazebo
`/world/<world>/set_pose` service -- one cell (or 90 deg) per mms command.

Why pose, not velocity: setting the pose directly means there is no setpoint to
overshoot and nothing to drift. It also talks straight to the sim (gz transport)
instead of the ROS<->gz /cmd_vel bridge, which is slow/unreliable on WSL without
a GPU. So each move is exact and fast regardless of physics real-time factor.

We always know the robot's exact pose (it starts at a known cell and we set
every pose since), so no odometry is needed.

Decoupled design: the brain (mms) fires every command up front without waiting.
The subscription callback only appends to an in-memory FIFO; a worker thread
animates the robot one command at a time and publishes /maze/step_complete after
each. This makes it impossible to drop or reorder a command (the old lockstep
had a race where a stale step_complete let the brain run a cell ahead of the
robot), and lets mms + the brain window finish instantly while Gazebo catches
up smoothly.

Subscribes /maze/mms_command ("moveForward"|"turnLeft"|"turnRight").
Publishes  /maze/step_complete (std_msgs/Bool) after each move finishes.
"""
import collections
import math
import subprocess
import threading
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import String, Bool

from micromouse import conventions as C


class CellMotionController(Node):
    def __init__(self):
        super().__init__("cell_motion_controller")
        self.declare_parameter("spec_path", "")
        self.declare_parameter("world_name", "micromouse")
        self.declare_parameter("model_name", "micromouse")
        self.declare_parameter("cell_size_m", 0.30)
        self.declare_parameter("robot_z", 0.04)
        self.declare_parameter("steps", 2)          # interpolation sub-steps
        self.declare_parameter("step_dt", 0.01)     # wall seconds per sub-step

        self.world = self.get_parameter("world_name").value
        self.model = self.get_parameter("model_name").value
        self.cell = float(self.get_parameter("cell_size_m").value)
        self.z = float(self.get_parameter("robot_z").value)
        self.steps = int(self.get_parameter("steps").value)
        self.step_dt = float(self.get_parameter("step_dt").value)

        sc = (0, 0)
        spec_path = self.get_parameter("spec_path").value
        if spec_path:
            try:
                from micromouse import spec as spec_mod
                _, data = spec_mod.read(spec_path)
                self.cell = float(data["cell_size_m"])
                sc = tuple(data["start_cell"])
            except Exception as e:  # noqa: BLE001
                self.get_logger().warn("spec read failed (%s); using defaults"
                                       % e)

        # exact world pose we track (we know it precisely)
        self.start_x = sc[0] * self.cell + self.cell / 2.0
        self.start_y = sc[1] * self.cell + self.cell / 2.0
        self.start_yaw = math.pi / 2.0               # North
        self.x = self.start_x
        self.y = self.start_y
        self.yaw = self.start_yaw

        self.svc = "/world/%s/set_pose" % self.world
        self.done_pub = self.create_publisher(Bool, "/maze/step_complete", 10)
        self.cell_pub = self.create_publisher(Point, "/maze/current_cell", 10)
        # Large depth: the brain dumps the whole path at once and the callback
        # only appends, so the middleware queue must hold a burst until drained.
        self.create_subscription(String, "/maze/mms_command", self._on_cmd, 256)

        # FIFO of pending commands + worker that plays them back into Gazebo.
        self._queue = collections.deque()
        self._cv = threading.Condition()
        self._snapped = False
        self._worker = threading.Thread(target=self._run_worker, daemon=True)
        self._worker.start()

        self._snap_attempts = 0
        self._init_timer = self.create_timer(6.0, self._snap_to_start)
        self.get_logger().info(
            "pose controller ready (cell=%.3f m, service=%s, steps=%d)"
            % (self.cell, self.svc, self.steps))

    # -- pose helpers --------------------------------------------------------
    def _world_to_cell(self):
        col = int(round((self.x - self.cell / 2.0) / self.cell))
        row = int(round((self.y - self.cell / 2.0) / self.cell))
        return col, row

    def _publish_cell(self):
        col, row = self._world_to_cell()
        self.cell_pub.publish(Point(x=float(col), y=float(row), z=0.0))

    def _snap_to_start(self):
        self._snap_attempts += 1
        if not self._set_pose(self.x, self.y, self.yaw):
            if self._snap_attempts < 10:
                self.get_logger().warn(
                    "set_pose failed (attempt %d) -- robot not spawned yet?"
                    % self._snap_attempts)
                return
            self.get_logger().error(
                "could not set_pose after %d attempts" % self._snap_attempts)
        self._init_timer.cancel()
        self._publish_cell()
        with self._cv:
            self._snapped = True
            self._cv.notify_all()
        self.get_logger().info("snapped robot to start cell %s"
                               % (self._world_to_cell(),))

    @staticmethod
    def _quat(yaw):
        return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))

    def _set_pose(self, x, y, yaw):
        qx, qy, qz, qw = self._quat(yaw)
        req = ('name: "%s", position: {x: %.5f, y: %.5f, z: %.5f}, '
               'orientation: {x: %.6f, y: %.6f, z: %.6f, w: %.6f}'
               % (self.model, x, y, self.z, qx, qy, qz, qw))
        try:
            result = subprocess.run(
                ["gz", "service", "-s", self.svc,
                 "--reqtype", "gz.msgs.Pose", "--reptype", "gz.msgs.Boolean",
                 "--timeout", "3000", "--req", req],
                capture_output=True, text=True, timeout=5.0)
            if result.returncode != 0:
                err = (result.stderr or result.stdout or "").strip()
                self.get_logger().debug("set_pose rc=%d %s"
                                        % (result.returncode, err))
                return False
            return True
        except Exception as e:  # noqa: BLE001
            self.get_logger().warn("set_pose failed: %s" % e)
            return False

    def _interp_to(self, tx, ty, tyaw):
        x0, y0, yaw0 = self.x, self.y, self.yaw
        dyaw = C.normalize_angle(tyaw - yaw0)        # shortest arc
        n = max(1, self.steps)
        for i in range(1, n + 1):
            f = i / n
            self._set_pose(x0 + (tx - x0) * f,
                           y0 + (ty - y0) * f,
                           yaw0 + dyaw * f)
            time.sleep(self.step_dt)
        self.x, self.y, self.yaw = tx, ty, C.normalize_angle(tyaw)

    # -- command handling ----------------------------------------------------
    def _on_cmd(self, msg: String):
        # Fast path only: enqueue and return so the middleware queue never
        # overflows even when the brain fires the whole path at once.
        with self._cv:
            self._queue.append(msg.data.strip())
            self._cv.notify_all()

    def _execute(self, cmd: str) -> bool:
        if cmd == "resetToStart":
            # Teleport straight back to the start cell so every run begins from
            # the same place regardless of where the last run ended.
            self.x, self.y, self.yaw = (self.start_x, self.start_y,
                                        self.start_yaw)
            self._set_pose(self.x, self.y, self.yaw)
        elif cmd == "turnLeft":
            self._interp_to(self.x, self.y, self.yaw + math.pi / 2.0)
        elif cmd == "turnRight":
            self._interp_to(self.x, self.y, self.yaw - math.pi / 2.0)
        elif cmd == "moveForward":
            self._interp_to(self.x + self.cell * math.cos(self.yaw),
                            self.y + self.cell * math.sin(self.yaw),
                            self.yaw)
        else:
            self.get_logger().warn("unknown command '%s'" % cmd)
            return False
        return True

    def _run_worker(self):
        # Wait until the robot has been snapped to the start cell.
        with self._cv:
            while not self._snapped and rclpy.ok():
                self._cv.wait(timeout=0.5)
        while rclpy.ok():
            with self._cv:
                while not self._queue and rclpy.ok():
                    self._cv.wait(timeout=0.5)
                if not rclpy.ok():
                    return
                cmd = self._queue.popleft()
            self._execute(cmd)
            # NOTE: we intentionally do NOT publish /maze/current_cell here.
            # The brain owns that topic so the trail window fills at mms speed
            # (instantly); republishing the robot's lagging cell would make the
            # trail rewind. Acknowledge every command (even unknown ones) so the
            # brain's end-of-run handshake counts stay aligned.
            self.done_pub.publish(Bool(data=True))


def main(argv=None):
    rclpy.init(args=argv)
    node = CellMotionController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
