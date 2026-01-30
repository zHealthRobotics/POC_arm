from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    robot_description = Command([
        "xacro ",
        PathJoinSubstitution([
            FindPackageShare("waveshare_servos"),
            "description",
            "urdf",
            "one_motor.urdf.xacro"
        ])
    ])

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            {"robot_description": robot_description},
            PathJoinSubstitution([
                FindPackageShare("waveshare_servos"),
                "bringup",
                "config",
                "one_motor_controllers.yaml"
            ])
        ],
        output="screen"
    )

    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description}],
        output="screen"
    )

    jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    traj = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller"],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen"
    )

    return LaunchDescription([
        control_node,
        rsp,
        jsb,
        traj,
        rviz
    ])

