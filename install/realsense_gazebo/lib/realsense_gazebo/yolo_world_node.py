#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import math
from geometry_msgs.msg import PointStamped
import tf2_ros
import tf2_geometry_msgs
from sensor_msgs.msg import Image, CameraInfo
from my_robot_interfaces.msg import PoseCommand  # Custom Message
from rclpy.duration import Duration
from cv_bridge import CvBridge
import cv2
import numpy as np

from ultralytics import YOLO

class YoloWorldNode(Node):
    def __init__(self):
        super().__init__('yolo_world_node')

        self.get_logger().info("Loading YOLO-World model...")
        self.model = YOLO("yolov8s-world.pt")

        self.model.set_classes([
            "drink can", "beverage container", "cup", "glass", "bottle", "human face"
        ])

        self.bridge = CvBridge()

        # Initialize variables
        self.depth_image = None 
        self.fx = self.fy = self.cx = self.cy = None

        # --- NEW: State for Change Detection ---
        # Stores (x, y, z) of the last message we actually sent
        self.last_published_coords = None 
        # Minimum movement required to trigger a new update (in meters)
        self.movement_threshold = 0.01
        
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # --- Subscribers ---
        self.create_subscription(Image, "/camera/image_raw", self.rgb_callback, 10)
        self.create_subscription(Image, "/camera/depth/image_raw", self.depth_callback, 10)
        self.create_subscription(CameraInfo, "/camera/camera_info", self.camera_info_callback, 10)

        # --- Publisher ---
        self.pose_pub = self.create_publisher(PoseCommand, "/pose_command", 10)
        self.debug_img_pub = self.create_publisher(Image, "/yolo/debug_image", 10)

        self.get_logger().info("YOLO-World node ready (Update-on-Change mode)")

    # ----------------- Callbacks -----------------

    def camera_info_callback(self, msg):
        self.fx = msg.k[0]
        self.fy = msg.k[4]
        self.cx = msg.k[2]
        self.cy = msg.k[5]

    def depth_callback(self, msg):
        try:
            self.depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
        except Exception as e:
            self.get_logger().error(f"Depth convert error: {e}")

    def rgb_callback(self, msg):
        self.get_logger().info("RGB CALLBACK HIT")
        if self.depth_image is None or self.fx is None:
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="rgb8")
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        except Exception as e:
            self.get_logger().error(f"RGB convert error: {e}")
            return

        results = self.model.predict(source=frame, conf=0.3, verbose=False)

        if len(results[0].boxes) > 0:
            box = results[0].boxes[0]

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            u = int((x1 + x2) / 2)
            v = int((y1 + y2) / 2)

            if 0 < u < self.depth_image.shape[1] and 0 < v < self.depth_image.shape[0]:
                patch = self.depth_image[
                    max(0, v-1):min(v+2, self.depth_image.shape[0]),
                    max(0, u-1):min(u+2, self.depth_image.shape[1])
                ]
                depth = float(np.nanmedian(patch))

                if depth > 0 and not np.isnan(depth):

                    # --- CAMERA FRAME COORDINATES ---
                    Y = (u - self.cx) * depth / self.fx
                    Z = (v - self.cy) * depth / self.fy
                    X = depth

                    # --- CHANGE DETECTION ---
                    should_publish = False
                    if self.last_published_coords is None:
                        should_publish = True
                    else:
                        lx, ly, lz = self.last_published_coords
                        dist = math.sqrt((X-lx)**2 + (Y-ly)**2 + (Z-lz)**2)
                        if dist > self.movement_threshold:
                            should_publish = True

                    if should_publish:

                        # ===== TF TRANSFORM (NEW PART) =====
                        point_cam = PointStamped()
                        point_cam.header.frame_id = "camera_link"
                        point_cam.header.stamp = self.get_clock().now().to_msg()
                        point_cam.point.x = X
                        point_cam.point.y = Y
                        point_cam.point.z = Z

                        try:
                            point_torso = self.tf_buffer.transform(
                                point_cam,
                                "torso_link",
                                timeout=Duration(seconds=0.1)
                            )
                        except Exception as e:
                            self.get_logger().warn(f"TF transform failed: {e}")
                            return
                        # ==================================

                        cmd_msg = PoseCommand()
                        cmd_msg.x = float(point_torso.point.x) 
                        cmd_msg.y = float(point_torso.point.y)
                        cmd_msg.z = float(point_torso.point.z)
                        cmd_msg.roll = 0.0
                        cmd_msg.pitch = 0.0
                        cmd_msg.yaw = 0.0
                        cmd_msg.cartesian_path = False

                        self.pose_pub.publish(cmd_msg)
                        self.last_published_coords = (X, Y, Z)

                        self.get_logger().info(
                            f"Published (torso_link): "
                            f"[{cmd_msg.x:.2f}, {cmd_msg.y:.2f}, {cmd_msg.z:.2f}]"
                        )

        # Debug image
        annotated = results[0].plot()
        debug_msg = self.bridge.cv2_to_imgmsg(annotated, encoding="bgr8")
        self.debug_img_pub.publish(debug_msg)

def main(args=None):
    rclpy.init(args=args)
    node = YoloWorldNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
