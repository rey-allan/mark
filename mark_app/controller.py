"""Defines the interface for a keyboard controller."""
import queue
import threading

from inputs import get_key

from common import MESSAGE_TYPE


# Modified from: https://github.com/kevinhughes27/TensorKart/blob/master/utils.py#L41
class KeyboardController(threading.Thread):
    """A keyboard controller.

    :param message_queue: The queue to put keyboard events.
    :type message_queue: queue.Queue
    """

    def __init__(self, message_queue: queue.Queue) -> None:
        super().__init__()

        self._message_queue = message_queue
        # Supported keys
        self._keys = {
            "KEY_W": 0,
            "KEY_A": 0,
            "KEY_S": 0,
            "KEY_D": 0,
            "KEY_UP": 0,
            "KEY_DOWN": 0,
            "KEY_LEFT": 0,
            "KEY_RIGHT": 0,
            "KEY_O": 0,
            "KEY_P": 0,
        }
        # Key to its command code
        self._key_to_command = {key: index + 1 for index, key in enumerate(self._keys.keys())}

    def run(self) -> None:
        while True:
            try:
                events = get_key()
                for event in events:
                    # For some reason, key D = KEY_RESERVED
                    if event.code == "KEY_RESERVED":
                        self._keys["KEY_D"] = event.state
                    elif event.code in self._keys:
                        self._keys[event.code] = event.state

                    self._message_queue.put((MESSAGE_TYPE.CONTROLLER_FEED_RECEIVED, self._keys))
            except:
                # Ignore any errors from `inputs` library
                pass

    def key_to_command(self, key: str) -> int:
        """Converts a key to its command code.

        :param key: The key to convert.
        :type key: str
        :return: The command code.
        :rtype: int
        """
        return self._key_to_command[key]
