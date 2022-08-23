"""Defines the interface for a keyboard controller."""
import queue
import threading
from typing import Dict, List

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
                    if event.code not in self._keys and event.code != "KEY_RESERVED":
                        continue

                    # For some reason, key D = KEY_RESERVED
                    if event.code == "KEY_RESERVED":
                        self._keys["KEY_D"] = event.state
                    else:
                        self._keys[event.code] = event.state

                    # Send the message only if the key is pressed
                    if event.state != 1:
                        continue
                    self._message_queue.put((MESSAGE_TYPE.CONTROLLER_FEED_RECEIVED, self._keys.copy()))
            except:
                # Ignore any errors from `inputs` library
                pass

    def keys(self) -> List[str]:
        """Returns the supported keys

        :return: A list with the supported keys
        :rtype: List[str]
        """
        return list(self._keys.keys())

    def read(self) -> Dict[str, int]:
        """Reads the latest controller keys and values

        :return: A dictionary of controller key to value (0 or 1)
        :rtype: Dict
        """
        return self._keys.copy()

    def key_to_command(self, key: str) -> int:
        """Converts a key to its command code.

        :param key: The key to convert.
        :type key: str
        :return: The command code.
        :rtype: int
        """
        return self._key_to_command[key]
