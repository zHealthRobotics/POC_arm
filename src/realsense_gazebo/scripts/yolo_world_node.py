#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import math
from geometry_msgs.msg import PointStamped
import tf2_ros
from sensor_msgs.msg import Image, CameraInfo
from my_robot_interfaces.msg import PoseCommand
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
        self.model.set_classes(["drink can", "beverage container", "glass", "bottle", "human face"])

        self.bridge = CvBridge()
        self.stable_count = 0
        self.required_stable_frames = 5
        self.last_published_coords = None 
        self.movement_threshold = 0.01

        self.depth_image = None 
        self.fx = self.fy = self.cx = self.cy = None
        
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # KINECT V1 TOPICS
        self.create_subscription(Image, "/image_raw", self.rgb_callback, 10)
        self.create_subscription(Image, "/depth/image_raw", self.depth_callback, 10)
        self.create_subscription(CameraInfo, "/camera_info", self.camera_info_callback, 10)

        self.pose_pub = self.create_publisher(PoseCommand, "/detected_target_pose", 10)
        self.debug_img_pub = self.create_publisher(Image, "/yolo/debug_image", 10)

        self.get_logger().info("YOLO Node Ready: NO ROTATION (Height Only)")

    def camera_info_callback(self, msg):
        self.fx = msg.k[0]
        self.fy = msg.k[4]
        self.cx = msg.k[2]
        self.cy = msg.k[5]

    def depth_callback(self, msg):
        try:
            self.depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
        except Exception:
            pass

    def rgb_callback(self, msg):
        if self.depth_image is None or self.fx is None:
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="rgb8")
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        except Exception as e:
            return

        results = self.model.predict(source=frame, conf=0.1, verbose=False)

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
                    # --- COORDINATE CONVERSION (Standard Camera Link) ---
                    # No extra rotation is applied here. 
                    # We simply map Optical Axis (Z) to Robot Forward (X).
                    
                    # 1. Forward Distance (X in robot frame) = Depth
                    x_cam = depth
                    
                    # 2. Left/Right (Y in robot frame)
                    # (u - cx) is positive RIGHT. We want positive LEFT.
                    y_cam = -((u - self.cx) * depth / self.fx) 
                    
                    # 3. Up/Down (Z in robot frame)
                    # (v - cy) is positive DOWN. We want positive UP.
                    z_cam = -((v - self.cy) * depth / self.fy) 

                    # --- CHANGE DETECTION ---
                    should_publish = False
                    if self.last_published_coords is None:
                        should_publish = True
                    else:
                        lx, ly, lz = self.last_published_coords
                        dist = math.sqrt((x_cam-lx)**2 + (y_cam-ly)**2 + (z_cam-lz)**2)
                        if dist > self.movement_threshold:
                            should_publish = True

                    if should_publish:
                        self.stable_count += 1
                    else:
                        self.stable_count = 0

                    if self.stable_count >= self.required_stable_frames:
                        point_cam = PointStamped()
                        point_cam.header.frame_id = "kinect_depth" 
                        point_cam.header.stamp = self.get_clock().now().to_msg()
                        point_cam.point.x = x_cam
                        point_cam.point.y = y_cam
                        point_cam.point.z = z_cam

                        try:
                            point_torso = self.tf_buffer.transform(
                                point_cam, "torso_link", timeout=Duration(seconds=0.1)
                            )
                        except Exception:
                            return

                        cmd_msg = PoseCommand()
                        cmd_msg.x = float(point_torso.point.x + 0.05)
                        cmd_msg.y = float(point_torso.point.y)
                        cmd_msg.z = float(point_torso.point.z)
                        cmd_msg.roll = 0.0
                        cmd_msg.pitch = 0.0
                        cmd_msg.yaw = 0.0
                        cmd_msg.cartesian_path = False 

                        self.pose_pub.publish(cmd_msg)
                        self.last_published_coords = (x_cam, y_cam, z_cam)
                        self.stable_count = 0 
                        
                        self.get_logger().info(f"Target: [{cmd_msg.x:.2f}, {cmd_msg.y:.2f}, {cmd_msg.z:.2f}]")

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
