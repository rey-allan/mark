"""Local client for testing the app."""
import os
import socket
import time

import cv2
import numpy as np


class Client:
    def __init__(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self._sock.connect(("localhost", 1060))
        self._send_camera_feed()

    def _send_camera_feed(self):
        capture = cv2.VideoCapture(0)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 500)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 450)

        try:
            while capture.isOpened():
                _, frame = capture.read()
                resize_frame = cv2.resize(frame, dsize=(500, 450), interpolation=cv2.INTER_AREA)

                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 30]
                _, imgencode = cv2.imencode(".jpg", resize_frame, encode_param)
                data = np.array(imgencode)
                send_len = self._send_image(data, 2048)

                if send_len == 0:
                    print("Video feed transmission failed")
                    break

                time.sleep(0.095)

            self._sock.close()
            os._exit(0)
        except Exception as e:
            print(e)
            self._sock.close()
            os._exit(0)

    def _send_image(self, image, buf_size):
        # Sends data to the given socket in chunks of `buf_size`
        block = int(len(image) / buf_size)
        send_len = 0

        for i in range(block):
            send_len += self._sock.send(image[i * buf_size : (i + 1) * buf_size])

        # Always send the last block in cases where `data` can't be divided exactly by `buf_size`
        send_len += self._sock.send(image[block * buf_size :])

        return send_len


if __name__ == "__main__":
    client = Client()
    client.start()
