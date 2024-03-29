import logging
import queue
import socket
import threading
from typing import ByteString, Optional

from common import MESSAGE_TYPE


class Server(threading.Thread):
    """A server that listens for messages from M.A.R.K.

    :param port: The port of the server
    :type port: int
    :param status_queue: The queue to put status messages from M.A.R.K.
    :type status_queue: queue.Queue
    :param camera_queue: The queue to put camera feed messages from M.A.R.K.
    :type camera_queue: queue.Queue
    """

    def __init__(self, port: int, status_queue: queue.Queue, camera_queue: queue.Queue) -> None:
        super().__init__()

        # Automatically discover the IP address of the host
        # Taken from: https://www.delftstack.com/howto/python/get-ip-address-python/
        self._host = socket.gethostbyname(socket.gethostname())
        self._port = port
        self._status_queue = status_queue
        self._camera_queue = camera_queue
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

            server_socket = _ServerSocket(sc, self._status_queue, self._camera_queue)
            server_socket.start()
            self._connection = server_socket

            logging.info("Ready to receive messages from M.A.R.K.")
            self._status_queue.put((MESSAGE_TYPE.CONNECTED, None))

    def send_to_mark(self, data: ByteString) -> None:
        """Sends data to M.A.R.K.

        :param data: The data to send
        :type data: ByteString
        """
        if self._connection is not None:
            self._connection.send_to_mark(data)

    def read_cam_image(self) -> bytearray:
        """Reads the latest camera image received from M.A.R.K.

        :return: An image as an array of bytes
        :rtype: bytearray
        """
        if self._connection is not None:
            return self._connection.cam_image

    def close(self) -> None:
        """Closes the connection to M.A.R.K."""
        if self._connection is not None:
            self._connection.close()


class _ServerSocket(threading.Thread):
    """A socket that supports the asynchronous communication with M.A.R.K.

    :param sc: The socket connection to M.A.R.K.
    :type sc: socket
    :param status_queue: The queue to put status messages from M.A.R.K.
    :type status_queue: queue.Queue
    :param camera_queue: The queue to put camera feed messages from M.A.R.K.
    :type camera_queue: queue.Queue
    """

    def __init__(self, sc: socket, status_queue: queue.Queue, camera_queue: queue.Queue) -> None:
        super().__init__()

        self.cam_image = None
        self._sc = sc
        self._status_queue = status_queue
        self._camera_queue = camera_queue

    def run(self) -> None:
        is_image_start = False
        image = None

        while True:
            try:
                bytes = self._sc.recv(2048)
                if bytes:
                    logging.debug("Received %s bytes from M.A.R.K.", len(bytes))
                    image, is_image_start = self._handle_camera_feed(bytes, image, is_image_start)
                else:
                    self._mark_disconnected()
                    break
            except:
                self._mark_disconnected()
                break

    def send_to_mark(self, data: ByteString) -> None:
        try:
            self._sc.send(data)
            logging.debug("Sent %s bytes to M.A.R.K.", len(data))
        except:
            pass

    def close(self) -> None:
        self._sc.close()

    def _handle_camera_feed(self, bytes: bytearray, image: bytearray, is_image_start: bool) -> None:
        # Handling of camera feed modified from:
        # https://github.com/codeandrobots/codeandrobots-app/blob/master/App/Services/Socket/index.js#L185

        # Look for the starting bytes of a JPEG
        start_index = _find_bytes(bytes, b"\xFF\xD8")

        if start_index is not None:
            is_image_start = True
            image = bytes[start_index:]
            return image, is_image_start

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
                self._camera_queue.put((MESSAGE_TYPE.CAMERA_FEED_RECEIVED, image))
                # Only save the latest complete image
                self.cam_image = image
            else:
                # Continue reconstructing the image bytes
                image += bytes

        return image, is_image_start

    def _mark_disconnected(self) -> None:
        logging.info("M.A.R.K. disconnected.")
        self._sc.close()
        self._status_queue.put((MESSAGE_TYPE.DISCONNECTED, None))


def _find_bytes(bytes: bytearray, to_find: ByteString) -> Optional[int]:
    try:
        return bytes.index(to_find)
    except ValueError:
        return None
