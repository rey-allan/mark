"""Main app for controlling M.A.R.K. and recording data."""
import logging
import queue
import sys

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
    def __init__(self, root):
        # Queue to receive messages from M.A.R.K.
        self._queue = queue.Queue()

        self._root = root
        self._root.columnconfigure(0, weight=1)

        self._build_connection_status_frame()

        self._feed_frame = Frame(self._root)
        self._feed_frame.grid(row=1, column=0)

        self._build_camera_feed_panel()

        self._plot_queue = _PlotQueue(max_size=50)
        self._build_controller_feed_panel()

        self._start_server()
        self._start_controller()

        # Update the UI based on events from M.A.R.K.
        self._update()

    def close(self):
        self._server.close()
        self._root.destroy()

    def _build_connection_status_frame(self):
        self._status_frame = Frame(self._root)
        self._status_frame.grid(row=0, column=0)
        self._status_fixed_label = Label(self._status_frame, text="Status: ", font="Roboto 14 bold")
        self._status_fixed_label.grid(row=0, column=0)
        self._status_label = Label(self._status_frame, text="Offline", fg="red", font="Roboto 14 bold")
        self._status_label.grid(row=0, column=1)

    def _build_camera_feed_panel(self):
        self._camera_label = Label(self._feed_frame, text="Camera Feed", font="Roboto 14 bold")
        self._camera_label.grid(row=0, column=0)
        self._camera_feed = Canvas(self._feed_frame, width=500, height=450)
        self._camera_feed.grid(row=1, column=0, padx=50, pady=10)
        # Initialize with a placeholder image while we wait to receive images from M.A.R.K.
        # We need to do this double assignment to prevent the image to be garbage collected
        # See: https://stackoverflow.com/questions/26479728/tkinter-canvas-image-not-displaying
        self._root.placeholder_image = placeholder_image = ImageTk.PhotoImage(file="img/placeholder.png")
        self._camera_feed_image = self._camera_feed.create_image(0, 0, anchor="nw", image=placeholder_image)

    def _build_controller_feed_panel(self):
        self._controller_label = Label(self._feed_frame, text="Controller Feed", font="Roboto 14 bold")
        self._controller_label.grid(row=0, column=1)
        # 500 x 450 (width x height) same as the camera feed
        self._controller_figure = Figure(figsize=(5, 4.5), dpi=100)
        self._controller_plot = self._controller_figure.add_subplot(111)
        self._controller_canvas = FigureCanvasTkAgg(self._controller_figure, self._feed_frame)
        self._controller_canvas.get_tk_widget().grid(row=1, column=1, padx=50, pady=10)

    def _start_server(self):
        self._server = Server(host="localhost", port=1060, message_queue=self._queue)
        # We set the server as a daemon so that it can be killed when the app is closed
        self._server.daemon = True
        self._server.start()

    def _start_controller(self):
        self._controller = KeyboardController(message_queue=self._queue)
        # We set the server as a daemon so that it can be killed when the app is closed
        self._controller.daemon = True
        self._controller.start()

    def _update(self) -> None:
        if not self._queue.empty():
            message_type, data = self._queue.get()
            self._handle_message(message_type, data)

        # Check for messages in the queue every 100ms
        self._root.after(100, self._update)

    def _handle_message(self, message_type: str, data: Any) -> None:
        if message_type is MESSAGE_TYPE.CONNECTED:
            self._status_label.config(text="Online", fg="green", font="Roboto 14 bold")
        elif message_type is MESSAGE_TYPE.DISCONNECTED:
            self._status_label.config(text="Offline", fg="red", font="Roboto 14 bold")
            # Reset camera feed to the placeholder
            self._camera_feed.itemconfig(self._camera_feed_image, image=self._root.placeholder_image)
        elif message_type is MESSAGE_TYPE.CAMERA_FEED_RECEIVED:
            # Display the received image in the camera feed
            self._root.camera_image = camera_image = ImageTk.PhotoImage(data=data, format="jpg")
            self._camera_feed.itemconfig(self._camera_feed_image, image=camera_image)
        elif message_type is MESSAGE_TYPE.CONTROLLER_FEED_RECEIVED:
            # Plot the received data in the controller feed
            self._plot_queue.put(list(data.values()))
            self._update_controller_plot(list(data.keys()))

            # TODO: Send the controller feed to M.A.R.K. as commands

    def _update_controller_plot(self, keys: List[str]) -> None:
        data = np.array(self._plot_queue.get())

        self._controller_plot.clear()

        for i, key in enumerate(keys):
            self._controller_plot.plot(data[:, i], linewidth=2, label=key)

        self._controller_plot.legend(loc="upper left", fontsize=8)
        self._controller_canvas.draw()


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
