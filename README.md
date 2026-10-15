# TurtleBot3 Autonomous Patrol System

A ROS 2 Jazzy-based autonomous patrol system for TurtleBot3 Burger in Gazebo. The robot follows a square patrol route, detects obstacles using LiDAR, performs obstacle avoidance, supports an emergency stop, and records movement telemetry.

## Features

- **LiDAR Obstacle Detection:** Divides laser scan measurements into front, left, and right sectors and calculates the minimum distance in each sector.
- **Autonomous Square Patrol:** Uses odometry to control the robot as it follows a square patrol route.
- **Obstacle Avoidance:** Detects obstacles ahead, stops forward movement, and turns toward the clearer side before resuming patrol.
- **Emergency Stop:** Provides a ROS 2 service to activate and clear the emergency stop.
- **Telemetry Logging:** Tracks total distance travelled, current speed, average speed, and estimated battery percentage.
- **Configurable Parameters:** Patrol distance, speeds, and tolerances can be adjusted through a YAML configuration file.
- **Single-Command Launch:** Starts the Gazebo simulation and all four application nodes.

## Technologies Used

- Ubuntu 24.04
- ROS 2 Jazzy
- Python
- TurtleBot3 Burger
- Gazebo
- ROS 2 topics, services, and parameters
- YAML configuration
- CSV telemetry logging

## Project Structure

```text
turtlebot_patrol/
├── config/
│   └── patrol_params.yaml
├── launch/
│   └── patrol_simulation.launch.py
├── resource/
│   └── turtlebot_patrol
├── test/
├── turtlebot_patrol/
│   ├── __init__.py
│   ├── lidar_obstacle_detector.py
│   ├── patrol_controller.py
│   ├── emergency_stop_server.py
│   └── telemetry_logger.py
├── package.xml
├── setup.cfg
├── setup.py
├── .gitignore
└── README.md
```

## Requirements

The following software is required:

- Ubuntu 24.04
- ROS 2 Jazzy
- TurtleBot3 ROS 2 packages
- Gazebo and the TurtleBot3 Gazebo simulation package
- `colcon`

Ensure ROS 2 Jazzy and the TurtleBot3 simulation dependencies are installed before proceeding.

## Build Instructions

Open a terminal and source ROS 2:

```bash
source /opt/ros/jazzy/setup.bash
```

Navigate to the workspace:

```bash
cd ~/turtlebot_ws
```

Build the package:

```bash
colcon build --packages-select turtlebot_patrol --symlink-install
```

Source the workspace:

```bash
source ~/turtlebot_ws/install/setup.bash
```

## Launch the Simulation

Set the TurtleBot3 model:

```bash
export TURTLEBOT3_MODEL=burger
```

Launch the complete patrol simulation:

```bash
ros2 launch turtlebot_patrol patrol_simulation.launch.py
```

The launch file starts the Gazebo simulation and the four application nodes.

## ROS 2 Nodes

### 1. LiDAR Obstacle Detector

**Node:** `lidar_obstacle_detector`

Subscribes to `/scan` and divides LiDAR measurements into three sectors:

- Front: -30° to +30°
- Left: +30° to +90°
- Right: -90° to -30°

Calculates the minimum distance in each sector and publishes the obstacle information to `/obstacle_status`.

A front obstacle is detected when its minimum measured distance falls below 0.5 metres.

### 2. Patrol Controller

**Node:** `patrol_controller`

Controls the robot's square patrol route using odometry.

The controller supports three operating states:

- **PATROL:** Moves along the patrol route.
- **AVOID:** Stops forward movement and turns toward the clearer side when an obstacle blocks the path.
- **HALTED:** Stops the robot while the emergency stop is active.

The controller subscribes to obstacle status, odometry, and emergency-stop state. Velocity commands are published to `/cmd_vel`.

### 3. Emergency-Stop Server

**Node:** `emergency_stop_server`

Provides the `/trigger_estop` service using `std_srvs/srv/SetBool`.

- `true`: Activates the emergency stop.
- `false`: Clears the emergency stop.

The server publishes the current state through `/estop_state`.

### 4. Telemetry Logger

**Node:** `telemetry_logger`

Monitors odometry and velocity commands to calculate movement statistics.

The telemetry includes:

- Total distance travelled
- Current linear speed
- Average linear speed
- Estimated battery percentage

The logger publishes a summary to `/robot_telemetry` and writes telemetry records to a CSV file named `telemetry_log.csv`.

The battery percentage is a simulated estimate, not a measurement of an actual battery.

## Important ROS 2 Topics

| Topic | Message Type | Purpose |
|---|---|---|
| `/scan` | `sensor_msgs/msg/LaserScan` | LiDAR sensor measurements |
| `/obstacle_status` | `std_msgs/msg/Float32MultiArray` | Front, left, and right minimum distances and obstacle flag |
| `/odom` | `nav_msgs/msg/Odometry` | Robot position and orientation |
| `/cmd_vel` | `geometry_msgs/msg/TwistStamped` | Robot velocity commands |
| `/estop_state` | `std_msgs/msg/Bool` | Emergency-stop state |
| `/robot_telemetry` | `std_msgs/msg/String` | Telemetry summary |

The `/obstacle_status` array contains four values:

1. Front minimum distance
2. Left minimum distance
3. Right minimum distance
4. Obstacle flag

## Emergency-Stop Usage

Keep the simulation running in one terminal.

Open another terminal and source the ROS environments:

```bash
source /opt/ros/jazzy/setup.bash
source ~/turtlebot_ws/install/setup.bash
```

### Activate the emergency stop

```bash
ros2 service call /trigger_estop std_srvs/srv/SetBool "{data: true}"
```

The controller should enter the `HALTED` state and stop the robot.

### Clear the emergency stop

```bash
ros2 service call /trigger_estop std_srvs/srv/SetBool "{data: false}"
```

The emergency-stop state is cleared, allowing the controller to resume its operation.

## Configuration

Patrol parameters are stored in `config/patrol_params.yaml`.

The default configuration is:

```yaml
patrol_controller:
  ros__parameters:
    side_length: 1.0
    linear_speed: 0.10
    angular_speed: 0.45
    position_tolerance: 0.08
    heading_tolerance_degrees: 5.0
```

| Parameter | Default | Description |
|---|---:|---|
| `side_length` | `1.0` | Length of each patrol side, in metres |
| `linear_speed` | `0.10` | Forward speed, in metres per second |
| `angular_speed` | `0.45` | Angular turning speed, in radians per second |
| `position_tolerance` | `0.08` | Position tolerance, in metres |
| `heading_tolerance_degrees` | `5.0` | Heading tolerance, in degrees |

The launch file loads this configuration automatically.

## Verification and Debugging

### List active nodes

```bash
ros2 node list
```

Expected application nodes:

```text
/emergency_stop_server
/lidar_obstacle_detector
/patrol_controller
/telemetry_logger
```

Gazebo may start additional nodes.

### List topics

```bash
ros2 topic list
```

### Inspect obstacle detection

```bash
ros2 topic echo /obstacle_status
```

### Inspect telemetry

```bash
ros2 topic echo /robot_telemetry
```

### Inspect patrol parameters

```bash
ros2 param list /patrol_controller
ros2 param get /patrol_controller side_length
ros2 param get /patrol_controller linear_speed
ros2 param get /patrol_controller angular_speed
```

### Check the emergency-stop service

```bash
ros2 service list
```

The list should include `/trigger_estop`.

## Demonstration

The project demonstration should show:

1. The robot starting its square patrol.
2. LiDAR detecting an obstacle.
3. The robot stopping and turning to avoid the obstacle.
4. The robot resuming patrol after the path clears.
5. The emergency stop halting the robot.
6. The telemetry output or generated CSV file.

Add screenshots of the simulation and terminal output to the repository before submitting.

## Limitations

- The patrol controller relies on odometry and the simulated environment.
- Obstacle avoidance is reactive and does not implement global path planning.
- The battery percentage is simulated.
- Performance depends on obstacle placement and simulation conditions.

## Author

Developed as a ROS 2 autonomous robotics project using TurtleBot3 and Gazebo.
