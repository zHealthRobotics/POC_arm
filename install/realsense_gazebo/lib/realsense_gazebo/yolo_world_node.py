#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import math

from sensor_msgs.msg import Image, CameraInfo
from my_robot_interfaces.msg import PoseCommand  # Custom Message

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
        self.movement_threshold = 0.05 

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
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # for OpenCV display + YOLO

        except Exception as e:
            self.get_logger().error(f"RGB convert error: {e}")
            return

        results = self.model.predict(source=frame, conf=0.3, verbose=False)
        self.get_logger().info(f"Detections: {len(results[0].boxes)}")

        if len(results[0].boxes) > 0:
            # We pick the FIRST detected object to track (simplification)
            # If you want to track specific IDs, you need the tracker logic back.
            box = results[0].boxes[0]

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            u = int((x1 + x2) / 2)
            v = int((y1 + y2) / 2)

            if 0 < u < self.depth_image.shape[1] and 0 < v < self.depth_image.shape[0]:
                patch = self.depth_image[max(0,v-1):min(v+2, self.depth_image.shape[0]), 
                                         max(0,u-1):min(u+2, self.depth_image.shape[1])]
                depth = float(np.nanmedian(patch))

                if depth > 0 and not np.isnan(depth):
                    # Calculate Current Position
                    Y = (u - self.cx) * depth / self.fx
                    Z = (((v - self.cy) * depth / self.fy)+0.2)
                    X = depth

                    # --- CHANGE DETECTION LOGIC ---
                    should_publish = False

                    if self.last_published_coords is None:
                        # First time detection: always publish
                        should_publish = True
                    else:
                        # Calculate distance from last published position
                        last_x, last_y, last_z = self.last_published_coords
                        distance = math.sqrt((X - last_x)**2 + (Y - last_y)**2 + (Z - last_z)**2)
                        
                        if distance > self.movement_threshold:
                            self.get_logger().info(f"Position changed by {distance:.3f}m. Updating...")
                            should_publish = True

                    # --- PUBLISH IF CHANGED ---
                    if should_publish:
                        cmd_msg = PoseCommand()
                        cmd_msg.x = float(X)
                        cmd_msg.y = float(Y)
                        cmd_msg.z = float(Z)
                        cmd_msg.roll = 3.14
                        cmd_msg.pitch = 0.0
                        cmd_msg.yaw = 0.0
                        cmd_msg.cartesian_path = False

                        self.pose_pub.publish(cmd_msg)
                        
                        # Update the last known coordinates
                        self.last_published_coords = (X, Y, Z)
                        
                        self.get_logger().info(f"Published Update: [{X:.2f}, {Y:.2f}, {Z:.2f}]")

        # Visualization
        annotated = results[0].plot()
        debug_msg = self.bridge.cv2_to_imgmsg(annotated, encoding="bgr8")
        self.debug_img_pub.publish(debug_msg)
        #cv2.imshow("YOLO-World Detection", annotated)
        #cv2.waitKey(1)

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
