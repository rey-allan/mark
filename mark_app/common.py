"""Defines common utilities."""


class MESSAGE_TYPE:
    """Defines the message types that can be sent to the broker queue"""

    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    CAMERA_FEED_RECEIVED = "CAMERA_FEED_RECEIVED"
    CONTROLLER_FEED_RECEIVED = "CONTROLLER_FEED_RECEIVED"
