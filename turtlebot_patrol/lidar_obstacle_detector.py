import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32MultiArray


class LidarObstacleDetector(Node):

    def __init__(self):
        super().__init__('lidar_obstacle_detector')

        self.scan_subscriber = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.obstacle_publisher = self.create_publisher(
            Float32MultiArray,
            '/obstacle_status',
            10
        )

        self.get_logger().info('LiDAR obstacle detector started.')

    def min_dist(self, ranges, max_range):
        valid = [
            distance for distance in ranges
            if math.isfinite(distance) and distance >= 0.0
        ]

        return min(valid) if valid else max_range

    def scan_callback(self, msg):
        front_ranges = []
        left_ranges = []
        right_ranges = []

        for i, distance in enumerate(msg.ranges):
            angle = msg.angle_min + i * msg.angle_increment
            angle_deg = math.degrees(angle) % 360.0

            if angle_deg <= 30.0 or angle_deg >= 330.0:
                front_ranges.append(distance)

            elif 30.0 < angle_deg <= 90.0:
                left_ranges.append(distance)

            elif 270.0 <= angle_deg < 330.0:
                right_ranges.append(distance)

        front = self.min_dist(front_ranges, msg.range_max)
        left = self.min_dist(left_ranges, msg.range_max)
        right = self.min_dist(right_ranges, msg.range_max)

        obstacle = front < 0.5

        msg_out = Float32MultiArray()
        msg_out.data = [
            float(front),
            float(left),
            float(right),
            1.0 if obstacle else 0.0
        ]

        self.obstacle_publisher.publish(msg_out)


def main(args=None):
    rclpy.init(args=args)
    node = LidarObstacleDetector()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()