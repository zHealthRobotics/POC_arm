#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import cv2
import numpy as np
from ultralytics import YOLOE

class RobustLiquidNode(Node):
    def __init__(self):
        super().__init__('robust_liquid_node')

        self.get_logger().info("Loading Robust YOLOE Node...")
        
        # 1. Load Model
        try:
            self.model = YOLOE('yoloe-v8s-seg.pt')
        except Exception:
            self.model = YOLOE('yoloe-v8s-seg.pt') # Retry or fail
        
        # Classes
        self.liquid_class = "orange liquid"
        self.glass_class = "glass"
        classes = [self.liquid_class, self.glass_class]
        self.model.set_classes(classes, self.model.get_text_pe(classes))

        # 2. Setup Webcam
        self.cap = cv2.VideoCapture(2)
        if not self.cap.isOpened():
            self.get_logger().error("Could not open webcam ID 2!")
            exit()

        # 3. Robustness Variables
        self.glass_streak = 0       # Current counter
        self.STREAK_TARGET = 5      # How many frames required
        self.GLASS_CONF_THRESH = 0.5 # High confidence for glass

        # 4. Publisher
        self.trigger_pub = self.create_publisher(Int32, '/liquid_trigger', 10)

        self.timer = self.create_timer(0.033, self.process_frame)
        self.get_logger().info("System Ready. Waiting for stable glass detection...")

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret: return

        # Inference
        results = self.model.predict(frame, conf=0.15, retina_masks=True, verbose=False)
        result = results[0]

        current_glass_box = None
        liquid_mask_poly = None

        # --- STEP 1: PARSE DETECTIONS ---
        if result.boxes is not None:
            masks = result.masks.xy if result.masks is not None else [None] * len(result.boxes)
            
            for box, mask, cls in zip(result.boxes, masks, result.boxes.cls):
                class_name = self.model.names[int(cls)]
                conf = float(box.conf[0])

                if class_name == self.glass_class:
                    # Robustness Check 1: High Confidence
                    if conf > self.GLASS_CONF_THRESH:
                        # Store the best glass found (or last one)
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        current_glass_box = (x1, y1, x2, y2)

                elif class_name == self.liquid_class and mask is not None:
                    liquid_mask_poly = np.array(mask, dtype=np.int32)

        # --- STEP 2: TEMPORAL STABILITY CHECK ---
        if current_glass_box is not None:
            self.glass_streak += 1
        else:
            self.glass_streak = 0 # Reset if glass is lost even for 1 frame

        is_stable = self.glass_streak >= self.STREAK_TARGET
        
        # Prepare Message (Default 0)
        trigger_msg = Int32()
        trigger_msg.data = 0

        # --- STEP 3: LOGIC EXECUTION ---
        if is_stable and current_glass_box:
            gx1, gy1, gx2, gy2 = current_glass_box
            glass_height = gy2 - gy1
            
            # Visual: Green Box (Stable)
            cv2.rectangle(frame, (gx1, gy1), (gx2, gy2), (0, 255, 0), 2)
            cv2.putText(frame, f"Stable ({self.glass_streak})", (gx1, gy1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Check Liquid Level
            if liquid_mask_poly is not None:
                # Liquid Top = Min Y of the polygon
                l_top_y = np.min(liquid_mask_poly[:, 1])
                
                # Liquid Height = Glass Bottom - Liquid Top
                # (Assuming liquid sits at the bottom of the glass)
                liquid_fill_px = gy2 - l_top_y
                
                # Calculate Ratio
                fill_ratio = liquid_fill_px / glass_height
                
                # Trigger Logic
                if fill_ratio >= 0.50:
                    trigger_msg.data = 1
                    status_color = (0, 255, 0) # Green Text
                    status_text = "Target Reached (1)"
                else:
                    status_color = (0, 0, 255) # Red Text
                    status_text = "Filling..."

                # Visuals for Liquid
                cv2.polylines(frame, [liquid_mask_poly], True, (0, 165, 255), 2)
                
                # Draw Level Line
                cv2.line(frame, (gx1, l_top_y), (gx2, l_top_y), status_color, 2)
                
                # Draw Info
                info = f"{status_text} | Level: {fill_ratio*100:.1f}%"
                cv2.putText(frame, info, (gx1, gy2 + 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        elif current_glass_box:
            # Visual: Yellow Box (Unstable/Acquiring)
            gx1, gy1, gx2, gy2 = current_glass_box
            cv2.rectangle(frame, (gx1, gy1), (gx2, gy2), (0, 255, 255), 2)
            cv2.putText(frame, f"Acquiring... {self.glass_streak}/{self.STREAK_TARGET}", (gx1, gy1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Publish
        self.trigger_pub.publish(trigger_msg)

        cv2.imshow("Robust Liquid Trigger", frame)
        cv2.waitKey(1)

    def destroy_node(self):
        self.cap.release()
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = RobustLiquidNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
