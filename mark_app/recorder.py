import csv
import io
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import PIL

from controller import KeyboardController
from server import Server


class Recorder(threading.Thread):
    """A class that asynchronously records camera images and controller values

    :param server: The server instance
    :type server: Server
    :param controller: The keyboard controller instance
    :type controller: KeyboardController
    :param sample_rate_ms: The rate at which to sample and record data in milliseconds
    :type sample_rate_ms: int
    """

    def __init__(self, server: Server, controller: KeyboardController, sample_rate_ms: int) -> None:
        super().__init__()

        self._server = server
        self._controller = controller
        self._sample_rate_ms = sample_rate_ms
        self._should_run = threading.Event()
        self._img_dir = None
        self._img_count = 0
        self._csv_file = None
        self._csv_writer = None

    def start_recording(self, output_dir: str) -> None:
        """Starts recording

        :param output_dir: The dictory where the data will be saved to. A child directory with the timestamp will be created.
        :type output_dir: str
        """
        # Prepare image directory
        self._img_dir = Path(output_dir).joinpath(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        self._img_dir.mkdir(parents=True, exist_ok=False)
        self._img_count = 0

        # Prepare csv file to store the data
        self._csv_file = open(self._img_dir.joinpath("data.csv"), "w", newline="")
        self._csv_writer = csv.writer(self._csv_file)
        # Write header: image location + controller keys
        self._csv_writer.writerow(["Image"] + self._controller.keys())

        # Set the run event so the thread starts working
        self._should_run.set()

    def stop_recording(self) -> None:
        """Stops recording

        Data is only saved when the recording is stopped
        """
        # Unset the run event to the thread stops working
        self._should_run.clear()
        self._csv_file.close()

    def run(self) -> None:
        while True:
            # Wait for the run event to be set
            self._should_run.wait()

            # Poll for the latest controller key and values
            controller_data = self._controller.read()
            # Poll the server for the latest camera image and save it to the output directory
            image_location = self._poll_camera_image()

            # Write a record to the csv file with the image location + controller data
            if image_location is not None:
                self._csv_writer.writerow([image_location] + list(controller_data.values()))

            time.sleep(self._sample_rate_ms / 1000.0)

    def _poll_camera_image(self) -> Optional[str]:
        image = self._server.read_cam_image()

        if image is None:
            return None

        cam_image = PIL.Image.open(io.BytesIO(image))
        image_location = str(self._img_dir.joinpath(f"{self._img_count}.png"))
        cam_image.save(image_location)

        self._img_count += 1

        return image_location
