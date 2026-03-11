#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray
import numpy as np

class TorquePDController(Node):

    def __init__(self):
        super().__init__('torque_pd_controller')

        self.joint_names = [
            'shoulder_pitch_joint',
            'shoulder_yaw_joint',
            'shoulder_roll_joint',
            'elbow_pitch_joint',
            'wrist_roll_joint',
            'wrist_pitch_joint',
            'wrist_yaw_joint'
        ]

        self.kp = 30.0
        self.kd = 5.0
        self.tau_max = 5.0

        self.q = np.zeros(7)
        self.qd = np.zeros(7)

        # Desired position (change this to test)
        self.q_des = np.array([0.5, 0, 0, 0, 0, 0, 0])

        self.sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_callback,
            10
        )

        self.pub = self.create_publisher(
            Float64MultiArray,
            '/arm_effort_controller/commands',
            10
        )

        self.timer = self.create_timer(0.01, self.control_loop)

    def joint_callback(self, msg):
        for i, name in enumerate(self.joint_names):
            idx = msg.name.index(name)
            self.q[i] = msg.position[idx]
            self.qd[i] = msg.velocity[idx]

    def control_loop(self):

        error = self.q_des - self.q
        derror = -self.qd

        tau = self.kp * error + self.kd * derror

        tau = np.clip(tau, -self.tau_max, self.tau_max)

        msg = Float64MultiArray()
        msg.data = tau.tolist()
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TorquePDController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
