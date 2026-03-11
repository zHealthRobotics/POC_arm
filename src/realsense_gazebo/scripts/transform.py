#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration

from geometry_msgs.msg import PointStamped
import tf2_ros
import tf2_geometry_msgs
from my_robot_interfaces.msg import PoseCommand
from my_robot_interfaces.msg import YoloTarget


class CameraToTorsoTFNode(Node):
    def __init__(self):
        super().__init__("camera_to_torso_tf_node")

        # TF
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Subscriber
        self.sub = self.create_subscription(
            YoloTarget,
            "/Camera_cord",
            self.target_callback,
            10
        )

        # Publisher
        self.pub = self.create_publisher(
            PoseCommand,
            "/pose_command",
            10
        )

        self.get_logger().info("Camera → Torso TF transformer node started")

    def target_callback(self, msg: YoloTarget):
        # ---- Build Point in camera_link ----
        point_cam = PointStamped()
        point_cam.header.frame_id = "camera_link"
        point_cam.header.stamp = self.get_clock().now().to_msg()

        point_cam.point.x = msg.x
        point_cam.point.y = msg.y
        point_cam.point.z = msg.z

        # ---- Transform to torso_link ----
        try:
            point_torso = self.tf_buffer.transform(
                point_cam,
                "torso_link",
                timeout=Duration(seconds=0.1)
            )
        except Exception as e:
            self.get_logger().warn(f"TF transform failed: {e}")
            return

        # ---- Publish PoseCommand ----
        cmd = PoseCommand()
        cmd.x = float(point_torso.point.x - 0.04)
        cmd.y = float(point_torso.point.y - 0.1)
        cmd.z = float(point_torso.point.z + 0.1)

        # Fixed orientation (safe default for MoveIt)
        cmd.roll = -1.57
        cmd.pitch = 3.14
        cmd.yaw = 1.57

        cmd.cartesian_path = False

        self.pub.publish(cmd)

        self.get_logger().info(
            f"Target {msg.id} transformed → torso_link: "
            f"[{cmd.x:.3f}, {cmd.y:.3f}, {cmd.z:.3f}]"
        )


def main(args=None):
    rclpy.init(args=args)
    node = CameraToTorsoTFNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

