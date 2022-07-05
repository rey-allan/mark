import logging
import queue
import socket
import threading
from typing import ByteString, Optional

from common import MESSAGE_TYPE


class Server(threading.Thread):
    """A server that listens for messages from M.A.R.K.

    :param host: The hostname of the server
    :type host: str
    :param port: The port of the server
    :type port: int
    :param message_queue: The queue to put messages from M.A.R.K.
    :type message_queue: queue.Queue
    """

    def __init__(self, host: str, port: int, message_queue: queue.Queue) -> None:
        super().__init__()

        self._host = host
        self._port = port
        self._message_queue = message_queue
        self._connection = None

    def run(self) -> None:
        """Runs the server asynchronously"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self._host, self._port))

        sock.listen(1)
        logging.info("Server listening on %s:%s", self._host, self._port)

        while True:
            sc, _ = sock.accept()
            logging.info("M.A.R.K. connected from %s:%s", sc.getpeername(), sc.getsockname())

            server_socket = _ServerSocket(sc, self._message_queue)
            server_socket.start()
            self._connection = server_socket

            logging.info("Ready to receive messages from M.A.R.K.")
            self._message_queue.put((MESSAGE_TYPE.CONNECTED, None))

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()


class _ServerSocket(threading.Thread):
    """A socket that supports the asynchronous communication with M.A.R.K.

    :param sc: The socket connection to M.A.R.K.
    :type sc: socket
    :param message_queue: The queue to put messages from M.A.R.K.
    :type message_queue: queue.Queue
    """

    def __init__(self, sc: socket, message_queue: queue.Queue) -> None:
        super().__init__()

        self._sc = sc
        self._message_queue = message_queue

    def run(self) -> None:
        is_image_start = False
        image = None

        while True:
            bytes = self._sc.recv(2048)
            if bytes:
                logging.info("Received %s bytes from M.A.R.K.", len(bytes))

                # Handling of camera feed modified from:
                # https://github.com/codeandrobots/codeandrobots-app/blob/master/App/Services/Socket/index.js#L185

                # Look for the starting bytes of a JPEG
                start_index = _find_bytes(bytes, b"\xFF\xD8")

                if start_index is not None:
                    is_image_start = True
                    image = bytes[start_index:]
                    continue

                # Are we still reading an image?
                if is_image_start:
                    # Look for the ending bytes of a JPEG to determine if we are done reading the image
                    end_index = _find_bytes(bytes, b"\xFF\xD9")

                    if end_index is not None:
                        is_image_start = False
                        # Finalize reconstructing the image bytes
                        # We add a 2 to actually include the ending bytes
                        image += bytes[: end_index + 2]
                        # Send the image to the message queue
                        self._message_queue.put((MESSAGE_TYPE.CAMERA_FEED_RECEIVED, image))
                    else:
                        # Continue reconstructing the image bytes
                        image += bytes
            else:
                logging.info("M.A.R.K. disconnected.")
                self._sc.close()
                self._message_queue.put((MESSAGE_TYPE.DISCONNECTED, None))
                break

    def close(self) -> None:
        self._sc.close()


def _find_bytes(bytes: bytearray, to_find: ByteString) -> Optional[int]:
    try:
        return bytes.index(to_find)
    except ValueError:
        return None
