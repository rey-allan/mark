"""Local client for testing the app."""
import logging
import os
import signal
import socket
import threading
import time
from typing import ByteString

import cv2
import numpy as np


class Client(threading.Thread):
    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        self._connect()

        camera_socket = _CameraSocket(self._sock)
        camera_socket.start()

        command_socket = _CommandSocket(self._sock)
        command_socket.start()

    def _connect(self) -> None:
        # Attempt to continuously connect to the server
        while True:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                self._sock.connect((socket.gethostbyname(socket.gethostname()), 1060))
                logging.info("Connected to server!")
                break
            except:
                logging.info("Failed to connect to server...retrying in 5 seconds")
                self._sock.close()
                time.sleep(5)


class _CameraSocket(threading.Thread):
    def __init__(self, sc: socket) -> None:
        super().__init__()

        self._sc = sc

    def run(self) -> None:
        capture = cv2.VideoCapture(0)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 500)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 450)

        try:
            while capture.isOpened():
                _, frame = capture.read()
                send_len = self._send_image(frame)

                if send_len == 0:
                    logging.info("Video feed transmission failed")
                    break

                time.sleep(0.095)

            self._sc.close()
            os._exit(0)
        except Exception as e:
            logging.info(e)
            self._sc.close()
            os._exit(0)

    def _send_image(self, frame):
        resize_frame = cv2.resize(frame, dsize=(500, 450), interpolation=cv2.INTER_AREA)

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 30]
        _, imgencode = cv2.imencode(".jpg", resize_frame, encode_param)
        data = np.array(imgencode)

        # Sends data to the given socket in chunks of `buf_size`
        block = int(len(data) / 2048)
        send_len = 0

        for i in range(block):
            send_len += self._sc.send(data[i * 2048 : (i + 1) * 2048])

        # Always send the last block in cases where `data` can't be divided exactly by `buf_size`
        send_len += self._sc.send(data[block * 2048 :])

        return send_len


class _CommandSocket(threading.Thread):
    def __init__(self, sc: socket.socket) -> None:
        super().__init__()

        self._sc = sc

    def run(self) -> None:
        while True:
            try:
                data = self._sc.recv(1)
                if data:
                    self._handle_command(data)
                else:
                    logging.info("Server disconnected")
                    self._sc.close()
                    os._exit(0)
            except Exception as e:
                logging.info(e)
                self._sc.close()
                os._exit(0)

    def _handle_command(self, command: ByteString) -> None:
        if command == b"\x00":
            logging.info("KeepAlive")
        if command == b"\x01":
            logging.info("Move forward")
        if command == b"\x02":
            logging.info("Turn left")
        if command == b"\x03":
            logging.info("Move backward")
        if command == b"\x04":
            logging.info("Turn right")
        if command == b"\x05":
            logging.info("Tilt up")
        if command == b"\x06":
            logging.info("Tilt down")
        if command == b"\x07":
            logging.info("Pan left")
        if command == b"\x08":
            logging.info("Pan right")
        if command == b"\x09":
            logging.info("Open gripper")
        if command == b"\x0A":
            logging.info("Close gripper")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    client = Client()
    client.start()

    def sig_handler(_, __):
        logging.info("Exiting...")
        os._exit(0)

    # Register signal handler for SIGINT (i.e. to handle keyboard interrupts)
    signal.signal(signal.SIGINT, sig_handler)
