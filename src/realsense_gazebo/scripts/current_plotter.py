#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import matplotlib.pyplot as plt
import numpy as np
import csv
from datetime import datetime


class CurrentRecorder(Node):

    def __init__(self):
        super().__init__('current_recorder')

        self.subscription = self.create_subscription(
            Float64MultiArray,
            '/motor_currents',
            self.listener_callback,
            10)

        self.joint_names = [
            'shoulder_pitch_joint',
            'shoulder_yaw_joint',
            'shoulder_roll_joint',
            'elbow_pitch_joint',
            'wrist_roll_joint',
            'wrist_pitch_joint',
            'wrist_yaw_joint'
        ]

        self.currents = [[] for _ in range(7)]
        self.samples = []

        self.counter = 0

        self.get_logger().info("Recording motor currents... Press Ctrl+C to stop.")

    def listener_callback(self, msg):

        if len(msg.data) != 7:
            return

        self.samples.append(self.counter)

        for i in range(7):
            self.currents[i].append(msg.data[i])

        self.counter += 1


def save_csv(node):

    filename = f"motor_currents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        header = ['sample'] + node.joint_names
        writer.writerow(header)

        for i in range(len(node.samples)):
            row = [node.samples[i]] + [node.currents[j][i] for j in range(7)]
            writer.writerow(row)

    print(f"\nSaved data to {filename}")


def plot_results(node):

    fig = plt.figure(figsize=(15, 10))
    fig.suptitle("Motor Current Recording", fontsize=16)

    # Create 3 columns layout manually
    grid = fig.add_gridspec(3, 3)

    axes = []

    # Column 1 (3 plots)
    axes.append(fig.add_subplot(grid[0, 0]))
    axes.append(fig.add_subplot(grid[1, 0]))
    axes.append(fig.add_subplot(grid[2, 0]))

    # Column 2 (3 plots)
    axes.append(fig.add_subplot(grid[0, 1]))
    axes.append(fig.add_subplot(grid[1, 1]))
    axes.append(fig.add_subplot(grid[2, 1]))

    # Column 3 (1 plot centered)
    axes.append(fig.add_subplot(grid[1, 2]))

    for i in range(7):
        axes[i].plot(node.samples, node.currents[i])
        axes[i].set_title(node.joint_names[i])
        axes[i].set_ylabel("Current (A)")
        axes[i].set_ylim(0.0, 1.2) 
        axes[i].grid(True)

    axes[-1].set_xlabel("Samples")

    plt.tight_layout()
    plt.show()


def main(args=None):
    rclpy.init(args=args)
    node = CurrentRecorder()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Stopping recording...")
    finally:
        save_csv(node)
        plot_results(node)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

