#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import message_filters

from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PointStamped
from visualization_msgs.msg import Marker, MarkerArray

from cv_bridge import CvBridge
import cv2
import numpy as np
from ultralytics import YOLO

class YoloWorldNode(Node):
    def __init__(self):
        super().__init__('yolo_world_node')

        self.get_logger().info("Loading YOLO-World...")
        self.model = YOLO("yolov8s-world.pt")

        self.model.set_classes([
            "drink can", "beverage container", "cup", "glass", "bottle", "human face"
        ])

        self.bridge = CvBridge()
        self.fx = self.fy = self.cx = self.cy = None

        # --- Subscribers ---
        self.create_subscription(CameraInfo, "/camera/camera_info", self.camera_info_callback, 10)

        rgb_sub = message_filters.Subscriber(self, Image, "/camera/image_raw")
        depth_sub = message_filters.Subscriber(self, Image, "/camera/depth/image_raw")

        self.ts = message_filters.ApproximateTimeSynchronizer([rgb_sub, depth_sub], 10, 0.1)
        self.ts.registerCallback(self.sync_callback)

        # --- DYNAMIC PUBLISHERS ---
        # We pre-create publishers for IDs 0 to 19.
        # This allows "concurrent" publishing: ID 1 goes to its own topic, ID 2 to its own, etc.
        self.id_publishers = []
        for i in range(20):
            topic_name = f"/yolo/id_{i}/position"
            pub = self.create_publisher(PointStamped, topic_name, 10)
            self.id_publishers.append(pub)
            self.get_logger().info(f"Created topic: {topic_name}")

        # Visualization Marker Publisher (for RViz)
        self.marker_pub = self.create_publisher(MarkerArray, "/yolo/all_markers", 10)

        self.get_logger().info("YOLO-World node ready.")

    def camera_info_callback(self, msg):
        if self.fx is None:
            self.fx = msg.k[0]
            self.fy = msg.k[4]
            self.cx = msg.k[2]
            self.cy = msg.k[5]

    def sync_callback(self, rgb_msg, depth_msg):
        if self.fx is None: return

        try:
            frame = self.bridge.imgmsg_to_cv2(rgb_msg, desired_encoding="bgr8")
            depth_image = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding="passthrough")
        except Exception as e:
            return

        # 1. Detect
        results = self.model.predict(source=frame, conf=0.3, verbose=False)
        
        if len(results[0].boxes) == 0:
            cv2.imshow("YOLO Detection", frame)
            cv2.waitKey(1)
            return

        marker_array = MarkerArray()

        # 2. Iterate through all detections
        # 'i' serves as our ID (0, 1, 2...) for this frame
        for i, box in enumerate(results[0].boxes):
            if i >= len(self.id_publishers):
                break # Ignore if we have more detections than pre-created publishers

            # --- 2D & 3D Math ---
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            u = int((x1 + x2) / 2)
            v = int((y1 + y2) / 2)

            if u < 0 or u >= depth_image.shape[1] or v < 0 or v >= depth_image.shape[0]:
                continue

            patch = depth_image[max(0,v-1):min(v+2, depth_image.shape[0]), 
                                max(0,u-1):min(u+2, depth_image.shape[1])]
            Z = float(np.nanmedian(patch))

            if Z <= 0 or np.isnan(Z):
                continue

            X = (u - self.cx) * Z / self.fx
            Y = (v - self.cy) * Z / self.fy
            
            label = self.model.names[int(box.cls[0])]

            # --- LOGGING ---
            # Shows data is being processed concurrently for this frame
            self.get_logger().info(
                f"Publishing to /yolo/id_{i}/position | {label} at ({X:.2f}, {Y:.2f}, {Z:.2f})"
            )

            # --- CONCURRENT PUBLISHING ---
            # Create the message
            point_msg = PointStamped()
            point_msg.header = rgb_msg.header # Sync timestamp
            point_msg.header.frame_id = "camera_link"
            point_msg.point.x = X
            point_msg.point.y = Y
            point_msg.point.z = Z

            # Publish to the SPECIFIC topic for this ID
            # e.g., if i=1, this sends to /yolo/id_1/position
            self.id_publishers[i].publish(point_msg)


            # --- VISUALIZATION ---
            # Marker for RViz
            marker = Marker()
            marker.header = point_msg.header
            marker.ns = "yolo_ids"
            marker.id = i
            marker.type = Marker.TEXT_VIEW_FACING
            marker.action = Marker.ADD
            marker.pose.position.x = X
            marker.pose.position.y = Y - 0.2
            marker.pose.position.z = Z
            marker.scale.z = 0.1
            marker.color.a = 1.0; marker.color.r = 1.0; marker.color.g = 1.0; marker.color.b = 0.0
            marker.text = f"ID:{i}"
            marker_array.markers.append(marker)

            # Draw on Window
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID:{i}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        self.marker_pub.publish(marker_array)
        cv2.imshow("YOLO Detection", frame)
        cv2.waitKey(1)

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
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
