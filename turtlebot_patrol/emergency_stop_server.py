import rclpy
from rclpy.node import Node

from std_msgs.msg import Bool   
from std_srvs.srv import SetBool

class EmergencyStopServer(Node):

    def __init__(self):
        super().__init__('emergency_stop_server')

        self.estop_state = False

        self.estop_publisher = self.create_publisher(
            Bool,
            '/estop_state',
            10
        )

        self.estop_service = self.create_service(
            SetBool,
            '/trigger_estop',
            self.estop_callback
        )

    def estop_callback(self, request, response):

        self.estop_state = request.data

        msg = Bool()
        msg.data = self.estop_state

        self.estop_publisher.publish(msg)

        response.success = True

        if self.estop_state:
            response.message = "EMERGENCY STOP ACTIVATED"
        else:
            response.message = "EMERGENCY STOP CLEARED"

        return response


def main(args=None):
    rclpy.init(args=args)

    node = EmergencyStopServer()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
