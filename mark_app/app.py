"""Main app for controlling M.A.R.K. and recording data."""
import logging
import queue
import sys
import threading
import time

# For buttons to render properly in MacOS, we need to import `ttk`
# See: https://stackoverflow.com/q/59006014
from tkinter import Canvas, Frame, Label, Tk, messagebox, ttk
from typing import Any, List

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import ImageTk

from common import MESSAGE_TYPE
from controller import KeyboardController
from server import Server


class App:
    def __init__(self, root: Tk) -> None:
        # Queue to receive status messages from M.A.R.K.
        self._status_queue = queue.Queue()
        # Queue to receive camera feed data from M.A.R.K.
        self._camera_queue = queue.Queue()
        # Queue to receive controller feed data
        self._controller_queue = queue.Queue()

        self._root = root
        self._root.columnconfigure(0, weight=1)

        self._build_connection_status_frame()

        self._feed_frame = Frame(self._root)
        self._feed_frame.grid(row=1, column=0)

        self._build_camera_feed_panel()
        self._build_controller_feed_panel()

        self._start_server()
        self._start_controller()
        self._start_camera_handler()
        self._start_controller_handler()

        # Update the UI based on status events from M.A.R.K.
        self._update_status()

    def close(self) -> None:
        self._server.close()
        self._root.destroy()

    def _build_connection_status_frame(self) -> None:
        self._status_frame = Frame(self._root)
        self._status_frame.grid(row=0, column=0)
        self._status_fixed_label = Label(self._status_frame, text="Status: ", font="Roboto 14 bold")
        self._status_fixed_label.grid(row=0, column=0)
        self._status_label = Label(self._status_frame, text="Offline", fg="red", font="Roboto 14 bold")
        self._status_label.grid(row=0, column=1)

    def _build_camera_feed_panel(self) -> None:
        self._camera_label = Label(self._feed_frame, text="Camera Feed", font="Roboto 14 bold")
        self._camera_label.grid(row=0, column=0)
        self._camera_feed = Canvas(self._feed_frame, width=500, height=450)
        self._camera_feed.grid(row=1, column=0, padx=50, pady=10)
        # Initialize with a placeholder image while we wait to receive images from M.A.R.K.
        # We need to do this double assignment to prevent the image to be garbage collected
        # See: https://stackoverflow.com/questions/26479728/tkinter-canvas-image-not-displaying
        self._root.placeholder_image = placeholder_image = ImageTk.PhotoImage(file="img/placeholder.png")
        self._camera_feed_image = self._camera_feed.create_image(0, 0, anchor="nw", image=placeholder_image)

    def _build_controller_feed_panel(self) -> None:
        self._controller_label = Label(self._feed_frame, text="Controller Feed", font="Roboto 14 bold")
        self._controller_label.grid(row=0, column=1)
        # 500 x 450 (width x height) same as the camera feed
        self._controller_figure = Figure(figsize=(5, 4.5), dpi=100)
        self._controller_plot = self._controller_figure.add_subplot(111)
        self._controller_canvas = FigureCanvasTkAgg(self._controller_figure, self._feed_frame)
        self._controller_canvas.get_tk_widget().grid(row=1, column=1, padx=50, pady=10)

    def _start_server(self) -> None:
        self._server = Server(
            host="localhost",
            port=1060,
            status_queue=self._status_queue,
            camera_queue=self._camera_queue,
        )
        # We set the server as a daemon so that it can be killed when the app is closed
        self._server.daemon = True
        self._server.start()

    def _start_controller(self) -> None:
        self._controller = KeyboardController(message_queue=self._controller_queue)
        # We set the server as a daemon so that it can be killed when the app is closed
        self._controller.daemon = True
        self._controller.start()

    def _start_camera_handler(self) -> None:
        self._camera_handler = _CameraHandler(
            message_queue=self._camera_queue,
            root=self._root,
            camera_feed=self._camera_feed,
            camera_feed_image=self._camera_feed_image,
        )
        # We set the handler as a daemon so that it can be killed when the app is closed
        self._camera_handler.daemon = True
        self._camera_handler.start()

    def _start_controller_handler(self) -> None:
        self._controller_handler = _ControllerHandler(
            message_queue=self._controller_queue,
            controller_canvas=self._controller_canvas,
            controller_plot=self._controller_plot,
            server=self._server,
            controller=self._controller,
        )
        # We set the handler as a daemon so that it can be killed when the app is closed
        self._controller_handler.daemon = True
        self._controller_handler.start()

    def _update_status(self) -> None:
        if not self._status_queue.empty():
            message_type, data = self._status_queue.get()
            self._handle_message(message_type, data)

        # Check for messages in the queue every 100ms
        self._root.after(100, self._update_status)

    def _handle_message(self, message_type: str, _: Any) -> None:
        if message_type is MESSAGE_TYPE.CONNECTED:
            self._status_label.config(text="Online", fg="green", font="Roboto 14 bold")
        elif message_type is MESSAGE_TYPE.DISCONNECTED:
            self._status_label.config(text="Offline", fg="red", font="Roboto 14 bold")
            # Reset camera feed to the placeholder
            self._camera_feed.itemconfig(self._camera_feed_image, image=self._root.placeholder_image)
        else:
            raise ValueError(f"Unknown status message type: {message_type}")


class _CameraHandler(threading.Thread):
    """Handles the camera feed and displays it in the camera feed panel.

    :param message_queue: The queue that receives images from the server
    :type message_queue: queue.Queue
    :param root: The root window
    :type root: Tk
    :param camera_feed: The canvas that displays the camera feed
    :type camera_feed: Canvas
    :param camera_feed_image: The image that is displayed in the camera feed
    :type camera_feed_image: Any
    """

    def __init__(self, message_queue: queue.Queue, root: Tk, camera_feed: Canvas, camera_feed_image: Any) -> None:
        super().__init__()

        self._message_queue = message_queue
        self._root = root
        self._camera_feed = camera_feed
        self._camera_feed_image = camera_feed_image

    def run(self) -> None:
        while True:
            if self._message_queue.empty():
                # Add some delay to the thread so we don't perform busy waiting and consume CPU
                # This avoids some flickering in the images when the server takes some time to send the next image
                time.sleep(0.1)
                continue
            message_type, data = self._message_queue.get()
            self._handle_message(message_type, data)

    def _handle_message(self, message_type: str, data: Any) -> None:
        if message_type is MESSAGE_TYPE.CAMERA_FEED_RECEIVED:
            # Display the received image in the camera feed
            self._root.camera_image = camera_image = ImageTk.PhotoImage(data=data, format="jpg")
            self._camera_feed.itemconfig(self._camera_feed_image, image=camera_image)
        else:
            raise ValueError(f"Unknown camera message type: {message_type}")


class _ControllerHandler(threading.Thread):
    """Handles the controller feed, displays it in the controller feed panel and sends commands to M.A.R.K.

    :param message_queue: The queue that receives controller feed
    :type message_queue: queue.Queue
    :param controller_canvas: The canvas that displays the controller feed
    :type controller_canvas: FigureCanvasTkAgg
    :param controller_plot: The plot that is displayed in the controller feed
    :type controller_plot: Any
    :param server: The server that sends commands to M.A.R.K.
    :type server: Server
    :param controller: The controller that reads the keyboard input
    :type controller: KeyboardController
    """

    def __init__(
        self,
        message_queue: queue.Queue,
        controller_canvas: FigureCanvasTkAgg,
        controller_plot: Any,
        server: Server,
        controller: KeyboardController,
    ) -> None:

        super().__init__()

        self._message_queue = message_queue
        self._controller_canvas = controller_canvas
        self._controller_plot = controller_plot
        self._server = server
        self._controller = controller
        self._plot_queue = _PlotQueue(max_size=50)

    def run(self) -> None:
        while True:
            if self._message_queue.empty():
                # Add some delay to the thread so we don't perform busy waiting and consume CPU
                time.sleep(0.1)
                continue
            message_type, data = self._message_queue.get()
            self._handle_message(message_type, data)

    def _handle_message(self, message_type: str, data: Any) -> None:
        if message_type is MESSAGE_TYPE.CONTROLLER_FEED_RECEIVED:
            # Plot the received data in the controller feed
            self._plot_queue.put(list(data.values()))
            self._update_controller_plot(list(data.keys()))
            # Send the controller feed to M.A.R.K. as commands
            self._send_controller_feed(data)
        else:
            raise ValueError(f"Unknown controller message type: {message_type}")

    def _update_controller_plot(self, keys: List[str]) -> None:
        data = np.array(self._plot_queue.get())

        self._controller_plot.clear()

        for i, key in enumerate(keys):
            self._controller_plot.plot(data[:, i], linewidth=2, label=key)

        self._controller_plot.legend(loc="upper left", fontsize=8)
        self._controller_canvas.draw()

    def _send_controller_feed(self, keys: dict[str, int]) -> None:
        # Only send the commands that are active
        for key, value in keys.items():
            if value == 0:
                continue
            # We send the command as a byte array of length 1 (e.g. 1 = b"\x01")
            self._server.send_to_mark(int.to_bytes(self._controller.key_to_command(key), 1, "big"))


class _PlotQueue:
    """A queue to manage the plot data.

    :param max_size: The maximum number of elements to store in the queue.
    :type max_size: int
    """

    def __init__(self, max_size: int) -> None:
        self._queue = []
        self._max_size = max_size

    def put(self, data: List[int]) -> None:
        self._queue.append(data)

        if len(self._queue) > self._max_size:
            self._queue.pop(0)

    def get(self) -> List[int]:
        return self._queue


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    window = Tk()
    window.title("M.A.R.K.")
    window.geometry("1200x600")

    app = App(window)

    def on_close():
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            app.close()
            sys.exit()

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()
