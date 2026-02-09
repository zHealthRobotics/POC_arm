from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():

    moveit_config = (
        MoveItConfigsBuilder(
            robot_name="poc_v2",
            package_name="poc_v2_moveit"
        )
        .to_moveit_configs()
    )

    bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            get_package_share_directory("poc_v2")
            + "/launch/poc_bringup.launch.py"
        )
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=[
            "-d",
            get_package_share_directory("poc_v2_moveit")
            + "/config/moveit.rviz"
        ],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
        ],
    )

    commander_node = Node(
        package="my_robot_commander_cpp",
        executable="commander",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
        ],
    )

    return LaunchDescription([
        bringup_launch,
        move_group_node,
        rviz_node,
        commander_node,
    ])

