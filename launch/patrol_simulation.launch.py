import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # Find the TurtleBot3 Gazebo package
    turtlebot3_gazebo_dir = get_package_share_directory(
        'turtlebot3_gazebo'
    )

    # Find the TurtleBot3 world launch file
    gazebo_launch_file = os.path.join(
        turtlebot3_gazebo_dir,
        'launch',
        'turtlebot3_world.launch.py'
    )

    # Ensure the TurtleBot3 model is set to Burger
    set_turtlebot_model = SetEnvironmentVariable(
        name='TURTLEBOT3_MODEL',
        value='burger'
    )

    # Launch Gazebo and the TurtleBot3 simulation
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_file)
    )

    # LiDAR obstacle detector
    lidar_detector = Node(
        package='turtlebot_patrol',
        executable='lidar_obstacle_detector',
        name='lidar_obstacle_detector',
        output='screen'
    )

    # Patrol controller with configurable parameters
    patrol_params_file = os.path.join(
        get_package_share_directory('turtlebot_patrol'),
        'config',
        'patrol_params.yaml'
)

    patrol_controller = Node(
        package='turtlebot_patrol',
        executable='patrol_controller',
        name='patrol_controller',
        parameters=[patrol_params_file],
        output='screen'
)
    # Emergency-stop server
    emergency_stop_server = Node(
        package='turtlebot_patrol',
        executable='emergency_stop_server',
        name='emergency_stop_server',
        output='screen'
    )

    # Telemetry logger
    telemetry_logger = Node(
        package='turtlebot_patrol',
        executable='telemetry_logger',
        name='telemetry_logger',
        output='screen'
    )

    return LaunchDescription([
        set_turtlebot_model,
        gazebo,
        lidar_detector,
        patrol_controller,
        emergency_stop_server,
        telemetry_logger
    ])