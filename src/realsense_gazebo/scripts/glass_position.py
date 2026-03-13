#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import cv2
import math  # Needed for Euclidean distance
from ultralytics import YOLO

class GlassAlignmentPoint(Node):
    def __init__(self):
        super().__init__('glass_alignment_point')

        self.get_logger().info("Loading YOLO-World...")
        self.model = YOLO('yolov8s-world.pt') 
        self.model.set_classes(["drinking glass"]) 

        # Open Webcam
        self.cap = cv2.VideoCapture(2)
        
        # Publisher
        self.publisher = self.create_publisher(Int32, '/glass_alignment_signal', 10)
        self.timer = self.create_timer(0.033, self.process_frame)

        # Settings
        self.tolerance = 40  # Radius in pixels (how close you must be to the point)
        self.get_logger().info("Scanning... Target is a POINT at (1/4 Width, Center Height).")

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret: return

        height, width, _ = frame.shape

        # --- DEFINING THE TARGET POINT ---
        # X = Quarter from left (25%)
        # Y = Center of height (50%)
        target_x = int(width / 4)
        target_y = int(height / 2)
        
        signal_msg = Int32()
        signal_msg.data = 0
        status_color = (0, 0, 255) # Red (Not aligned)

        # --- YOLO Inference ---
        results = self.model.predict(frame, conf=0.5, verbose=False)

        if len(results[0].boxes) > 0:
            box = results[0].boxes[0]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Glass Center
            glass_x = int((x1 + x2) / 2)
            glass_y = int((y1 + y2) / 2)

            # --- MATH: Euclidean Distance (2D) ---
            # d = sqrt((x2-x1)^2 + (y2-y1)^2)
            distance = math.sqrt((glass_x - target_x)**2 + (glass_y - target_y)**2)

            # Check if inside the tolerance circle
            if distance < self.tolerance:
                signal_msg.data = 1
                status_color = (0, 255, 0) # Green
                cv2.putText(frame, "LOCKED!", (glass_x + 10, glass_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Draw Glass Center
            cv2.circle(frame, (glass_x, glass_y), 5, status_color, -1)
            # Draw Line connecting Glass to Target
            cv2.line(frame, (glass_x, glass_y), (target_x, target_y), (255, 255, 255), 1)

        self.publisher.publish(signal_msg)

        # --- VISUALIZATION: Draw The Target Point ---
        # 1. Draw a Crosshair at the target
        cv2.drawMarker(frame, (target_x, target_y), (0, 255, 255), 
                      cv2.MARKER_CROSS, 20, 2)
        
        # 2. Draw the Tolerance Zone (Circle)
        cv2.circle(frame, (target_x, target_y), self.tolerance, (0, 255, 255), 2)

        cv2.imshow("Point Alignment", frame)
        cv2.waitKey(1)

    def destroy_node(self):
        self.cap.release()
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = GlassAlignmentPoint()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
