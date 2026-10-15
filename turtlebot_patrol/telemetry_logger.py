import rclpy
from rclpy.node import Node
import csv
import os

from nav_msgs.msg import Odometry
from geometry_msgs.msg import TwistStamped
from std_msgs.msg import String

class TelemetryLogger(Node):

    def __init__(self):
        super().__init__('telemetry_logger')

        self.telemetry_publisher = self.create_publisher(
            String,
            '/robot_telemetry',
            10
        )

        self.odom_subscriber = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.cmd_subscriber = self.create_subscription(
            TwistStamped,
            '/cmd_vel',
            self.cmd_callback,
            10
        )
        self.start_time = self.get_clock().now()
        self.total_distance = 0.0
        self.current_speed = 0.0

        self.previous_x = None
        self.previous_y = None

        self.speed_sum = 0.0
        self.speed_samples = 0

        self.battery = 100.0
        self.motion_time = 0.0
        self.last_update_time = self.get_clock().now()

        self.csv_file = os.path.expanduser(
            '~/turtlebot_ws/telemetry_log.csv'
        )

        self.csv_file_handle = open(
            self.csv_file,
            'a',
            newline=''
        )

        self.csv_writer = csv.writer(self.csv_file_handle)

        if os.path.getsize(self.csv_file) ==0:
            self.csv_writer.writerow([
                'timestamp',
                'total_distance_m',
                "current_speed_mps",
                "average_speed_mps",
                "battery_percent"
            ])

        self.telemetry_timer = self.create_timer(
            2.0,
            self.print_telemetry
        )

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        if self.previous_x is not None:
            dx = x - self.previous_x
            dy = y - self.previous_y

            distance = (dx ** 2 + dy ** 2) ** 0.5
            self.total_distance += distance

        self.previous_x = x
        self.previous_y = y

    def cmd_callback(self, msg):
        self.current_speed = abs(msg.twist.linear.x)

        self.speed_sum += self.current_speed
        self.speed_samples += 1

    def print_telemetry(self):
        now = self.get_clock().now()

        # Time since the previous telemetry update
        elapsed = (
            now - self.last_update_time
        ).nanoseconds / 1e9

        self.last_update_time = now

        # Battery simulation: 1% per 10 seconds of motion
        if self.current_speed > 0.0:
            self.motion_time += elapsed

        self.battery = max(
            0.0,
            100.0 - (self.motion_time / 10.0)
        )

        # Average speed since the logger started
        total_elapsed = (
            now - self.start_time
        ).nanoseconds / 1e9

        if total_elapsed > 0:
            average_speed = self.total_distance / total_elapsed
        else:
            average_speed = 0.0

        timestamp = now.nanoseconds / 1e9

        self.get_logger().info(
            f"Distance: {self.total_distance:.2f} m | "
            f"Current Speed: {self.current_speed:.2f} m/s | "
            f"Average Speed: {average_speed:.2f} m/s | "
            f"Battery: {self.battery:.1f}%"
        )

        telemetry_msg = String()

        telemetry_msg.data = (
            f"Distance: {self.total_distance:.2f} m | "
            f"Current Speed: {self.current_speed:.2f} m/s | "
            f"Average Speed: {average_speed:.2f} m/s | "
            f"Battery: {self.battery:.1f}%"
        )

        self.telemetry_publisher.publish(telemetry_msg)

        self.csv_writer.writerow([
            timestamp,
            f"{self.total_distance:.2f}",
            f"{self.current_speed:.2f}",
            f"{average_speed:.2f}",
            f"{self.battery:.1f}"
        ])

        self.csv_file_handle.flush()

        
def main(args=None):
    rclpy.init(args=args)

    node = TelemetryLogger()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.csv_file_handle.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__=='__main__':
    main()