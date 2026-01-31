from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    # Robot description (REAL hardware URDF)
    robot_description = Command([
        "xacro ",
        PathJoinSubstitution([
            FindPackageShare("poc_arm"),
            "urdf",
            "poc_arm.urdf.xacro"
        ])
    ])

    # ros2_control node (REAL hardware)
    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            {"robot_description": robot_description},
            PathJoinSubstitution([
                FindPackageShare("poc_arm"),
                "config",
                "ros2_controllers.yaml"
            ])
        ],
        output="screen"
    )

    # Robot state publisher
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description}]
    )

    # Controllers
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen"
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller"],
        output="screen"
    )

    # RViz
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=[
            "-d",
            PathJoinSubstitution([
                FindPackageShare("poc_arm"),
                "rviz",
                "urdf_config.rviz"
            ])
        ]
    )

    return LaunchDescription([
        control_node,
        robot_state_publisher,
        joint_state_broadcaster_spawner,
        arm_controller_spawner,
        rviz
    ])

