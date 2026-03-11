#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray
import numpy as np
import pinocchio as pin


class GravityCompNode(Node):

    def __init__(self):
        super().__init__('gravity_pinocchio')

        urdf_path = "/home/suvi/poc_arm/poc_v2_generated.urdf"

        # Build model
        self.model = pin.buildModelFromUrdf(urdf_path)
        self.data = self.model.createData()

        self.n = self.model.nq

        self.q = np.zeros(self.n)
        self.qd = np.zeros(self.n)

        self.q_des = None

        # 🔹 Stabilization gains
        self.kp = 15.0
        self.kd = 3.0

        self.tau_max = 8.0

        self.joint_names = [
            'shoulder_pitch_joint',
            'shoulder_yaw_joint',
            'shoulder_roll_joint',
            'elbow_pitch_joint',
            'wrist_roll_joint',
            'wrist_pitch_joint',
            'wrist_yaw_joint'
        ]

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

    def joint_callback(self, msg):

        # Map joint order properly
        for i, name in enumerate(self.joint_names):
            if name in msg.name:
                idx = msg.name.index(name)
                self.q[i] = msg.position[idx]
                self.qd[i] = msg.velocity[idx]

        # Lock initial pose
        if self.q_des is None:
            self.q_des = self.q.copy()

        # Gravity torque
        tau_g = pin.computeGeneralizedGravity(self.model, self.data, self.q)

        # PD stabilization
        tau_pd = self.kp * (self.q_des - self.q) - self.kd * self.qd

        tau = tau_g + tau_pd

        # Clamp torque
        tau = np.clip(tau, -self.tau_max, self.tau_max)

        msg_out = Float64MultiArray()
        msg_out.data = tau.tolist()
        self.pub.publish(msg_out)


def main():
    rclpy.init()
    node = GravityCompNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
