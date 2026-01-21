from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    pkg_share = get_package_share_directory('realsense_gazebo')
    # We don't strictly need gazebo_ros path anymore for the include, 
    # but it's good practice if you switch back later.
    
    world_path = os.path.join(pkg_share, 'worlds', 'test_world.world')

    camera_model = os.path.join(
        pkg_share,
        'models',
        'camera_bot_rs',
        'model.sdf'
    )

    # -------------------------
    # 1. FORCE START GAZEB SERVER (gzserver)
    # -------------------------
    # We use ExecuteProcess to run the command directly.
    # We explicitly pass '-s libgazebo_ros_factory.so' to enable spawning.
    # We also pass '-s libgazebo_ros_init.so' for basic ROS 2 integration.
    gzserver_cmd = ExecuteProcess(
        cmd=[
            'gzserver',
            '--verbose',
            '-s', 'libgazebo_ros_init.so',
            '-s', 'libgazebo_ros_factory.so',
            world_path
        ],
        output='screen'
    )

    # -------------------------
    # 2. START GAZEBO CLIENT (gzclient)
    # -------------------------
    # This opens the GUI.
    gzclient_cmd = ExecuteProcess(
        cmd=['gzclient'],
        output='screen'
    )

    # -------------------------
    # 3. SPAWN ENTITY
    # -------------------------
    spawn_camera = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'camera_bot_rs',
            '-file', camera_model,
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.2'
        ],
        output='screen'
    )

    # -------------------------
    # 4. TF PUBLISHER
    # -------------------------
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--yaw', '0', '--pitch', '0', '--roll', '0',
            '--frame-id', 'world', '--child-frame-id', 'camera_link'
        ],
        output='screen'
    )

    return LaunchDescription([
        gzserver_cmd,
        gzclient_cmd,
        spawn_camera, # We can try without the timer now, or keep it if your PC is very slow
        static_tf
    ])
