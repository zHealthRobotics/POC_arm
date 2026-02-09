import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():

    pkg_share = FindPackageShare('poc_moveit_config')
    
    gazebo_model_path = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH',
        value=os.pathsep.join([
            os.environ.get('GAZEBO_MODEL_PATH', ''),
            str(PathJoinSubstitution([
                FindPackageShare('poc_arm')
            ]))
        ])
    )    

    urdf_xacro = PathJoinSubstitution([
        pkg_share,
        'config',
        'my_robot.urdf1.xacro'
    ])

    controllers_yaml = PathJoinSubstitution([
        pkg_share,
        'config',
        'ros2_controllers_gazebo.yaml'
    ])

    world_file = PathJoinSubstitution([
        pkg_share, 'config', 'test2.world'
    ])

    # Gazebo with saved world
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'),
                'launch',
                'gazebo.launch.py'
            ])
        ),
        launch_arguments={
            'world': world_file
        }.items()
    )

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': ParameterValue(
                Command(['xacro ', urdf_xacro]),
                value_type=str
            )
        }]
    )



    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'my_robot',

            '-x', '-0.05',
            '-y', '-0.08',
            '-z', '0.0',
        ]
    )


    # Load controllers AFTER spawn
    load_joint_state_broadcaster = ExecuteProcess(
        cmd=[
            'ros2', 'control', 'load_controller',
            '--set-state', 'active',
            'joint_state_broadcaster'
        ],
        output='screen'
    )

    load_arm_controller = ExecuteProcess(
        cmd=[
            'ros2', 'control', 'load_controller',
            '--set-state', 'active',
            'arm_controller'
        ],
        output='screen'
    )

    return LaunchDescription([
        gazebo_model_path,
        gazebo,
        robot_state_publisher,
        spawn_entity,

        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_entity,
                on_exit=[
                    load_joint_state_broadcaster,
                    load_arm_controller
                ]
            )
        )
    ])

