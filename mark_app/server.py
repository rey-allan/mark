import logging
import queue
import socket
import threading


class MESSAGE_TYPE:
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


class Server(threading.Thread):
    def __init__(self, host: str, port: int, message_queue: queue.Queue) -> None:
        """A server that listens for messages from M.A.R.K.

        :param host: The hostname of the server
        :type host: str
        :param port: The port of the server
        :type port: int
        :param message_queue: The queue to put messages from M.A.R.K.
        :type message_queue: queue.Queue
        """
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
    def __init__(self, sc: socket, message_queue: queue.Queue) -> None:
        """A socket that supports the asynchronous communication with M.A.R.K.

        :param sc: The socket connection to M.A.R.K.
        :type sc: socket
        :param message_queue: The queue to put messages from M.A.R.K.
        :type message_queue: queue.Queue
        """
        super().__init__()

        self._sc = sc
        self._message_queue = message_queue

    def run(self):
        while True:
            # TODO: Handle camera feed from M.A.R.K.
            bytes = self._sc.recv(1024)
            if bytes:
                logging.info("Received %s bytes from M.A.R.K.", len(bytes))
            else:
                logging.info("M.A.R.K. disconnected.")
                self._sc.close()
                self._message_queue.put((MESSAGE_TYPE.DISCONNECTED, None))
                break

    def close(self):
        self._sc.close()
