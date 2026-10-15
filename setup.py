from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'turtlebot_patrol'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        # Install launch files
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')
        ),

        # Install configuration files
        (
            os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='devil-os',
    maintainer_email='308234900+devil-97os@users.noreply.github.com',
    description='TurtleBot3 autonomous patrol with obstacle avoidance',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'lidar_obstacle_detector = turtlebot_patrol.lidar_obstacle_detector:main',
            'patrol_controller = turtlebot_patrol.patrol_controller:main',
            'emergency_stop_server = turtlebot_patrol.emergency_stop_server:main',
            'telemetry_logger = turtlebot_patrol.telemetry_logger:main',
        ],
    },
)