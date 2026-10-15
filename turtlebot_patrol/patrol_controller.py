import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32MultiArray, Bool
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry


PATROL = 0
AVOID = 1
HALTED = 2


class PatrolController(Node):
    def __init__(self):
        super().__init__('patrol_controller')

        self.state = PATROL
        self.front_distance = 3.5
        self.left_distance = 3.5
        self.right_distance = 3.5
        self.obstacle_detected = False
        self.estop_active = False
        self.avoid_direction = 0
        self.avoid_clear_count = 0

        # Square-patrol settings, configurable through ROS parameters.
        self.declare_parameter('side_length', 1.0)
        self.declare_parameter('linear_speed', 0.10)
        self.declare_parameter('angular_speed', 0.45)
        self.declare_parameter('position_tolerance', 0.08)
        self.declare_parameter('heading_tolerance_degrees', 5.0)

        self.side_length = self.get_parameter('side_length').value
        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.position_tolerance = self.get_parameter(
            'position_tolerance'
        ).value
        self.heading_tolerance = math.radians(
            self.get_parameter('heading_tolerance_degrees').value
        )

        self.x = None
        self.y = None
        self.yaw = None
        self.side_start_x = None
        self.side_start_y = None
        self.target_yaw = None
        self.corner_turning = False
        self.route_ready = False

        self.obstacle_subscriber = self.create_subscription(
            Float32MultiArray, '/obstacle_status', self.obstacle_callback, 10
        )
        self.estop_subscriber = self.create_subscription(
            Bool, '/estop_state', self.estop_callback, 10
        )
        self.odom_subscriber = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10
        )
        self.cmd_publisher = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info('Patrol controller started; waiting for odometry.')

    @staticmethod
    def normalize_angle(angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    def obstacle_callback(self, msg):
        if len(msg.data) < 4:
            self.get_logger().warning('Invalid obstacle_status message.')
            return
        self.front_distance = msg.data[0]
        self.left_distance = msg.data[1]
        self.right_distance = msg.data[2]
        self.obstacle_detected = msg.data[3] >= 1.0

    def estop_callback(self, msg):
        was_active = self.estop_active
        self.estop_active = msg.data
        if self.estop_active and not was_active:
            self.get_logger().warning('Emergency stop activated.')
        elif was_active and not self.estop_active:
            self.get_logger().info('Emergency stop released.')

    def odom_callback(self, msg):
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation
        self.x = position.x
        self.y = position.y
        # Quaternion to yaw, without adding another package dependency.
        sin_yaw = 2.0 * (orientation.w * orientation.z + orientation.x * orientation.y)
        cos_yaw = 1.0 - 2.0 * (orientation.y * orientation.y + orientation.z * orientation.z)
        self.yaw = math.atan2(sin_yaw, cos_yaw)

        if not self.route_ready:
            self.side_start_x = self.x
            self.side_start_y = self.y
            self.route_ready = True
            self.get_logger().info('Odometry received. Starting 1 m square patrol.')

    def publish_velocity(self, linear=0.0, angular=0.0):
        cmd = TwistStamped()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.twist.linear.x = float(linear)
        cmd.twist.angular.z = float(angular)
        self.cmd_publisher.publish(cmd)

    def control_loop(self):
        # E-stop always overrides all movement.
        if self.estop_active:
            self.state = HALTED
            self.publish_velocity()
            return

        # Don't move until odometry establishes the starting pose.
        if not self.route_ready or self.x is None or self.yaw is None:
            self.publish_velocity()
            return

        # Obstacle avoidance temporarily pauses the square route.
        if self.obstacle_detected:
            if self.state != AVOID:
                self.avoid_direction = 1 if self.left_distance > self.right_distance else -1
                self.avoid_clear_count = 0
                self.get_logger().info('Obstacle detected: avoiding toward the clearer side.')
            self.state = AVOID
            self.publish_velocity(0.0, self.angular_speed * self.avoid_direction)
            return

        if self.state == AVOID:
            # Require several clear scans before returning to patrol.
            self.avoid_clear_count += 1
            if self.avoid_clear_count < 5:
                self.publish_velocity(0.0, self.angular_speed * self.avoid_direction)
                return
            self.state = PATROL
            # Rebase this side after avoidance so the robot doesn't try to
            # recover a stale straight-line distance through the obstacle.
            self.side_start_x = self.x
            self.side_start_y = self.y
            self.corner_turning = False
            self.get_logger().info('Path clear. Resuming square patrol from current position.')

        if self.corner_turning:
            heading_error = self.normalize_angle(self.target_yaw - self.yaw)
            if abs(heading_error) <= self.heading_tolerance:
                self.corner_turning = False
                self.side_start_x = self.x
                self.side_start_y = self.y
                self.get_logger().info('Corner complete. Continuing to next side.')
                self.publish_velocity()
            else:
                turn = self.angular_speed if heading_error > 0 else -self.angular_speed
                self.publish_velocity(0.0, turn)
            return

        travelled = math.hypot(self.x - self.side_start_x, self.y - self.side_start_y)
        if travelled >= self.side_length - self.position_tolerance:
            self.target_yaw = self.normalize_angle(self.yaw + math.pi / 2.0)
            self.corner_turning = True
            self.get_logger().info('Side complete. Turning 90 degrees.')
            self.publish_velocity()
            return

        self.state = PATROL
        self.publish_velocity(self.linear_speed, 0.0)


def main(args=None):
    rclpy.init(args=args)
    node = PatrolController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_velocity()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()