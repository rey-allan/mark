"""Main app for controlling M.A.R.K. and recording data."""
import logging
import queue
import sys

# For buttons to render properly in MacOS, we need to import `ttk`
# See: https://stackoverflow.com/q/59006014
from tkinter import Canvas, Frame, Label, Tk, messagebox, ttk
from typing import Any

from PIL import ImageTk

from server import MESSAGE_TYPE, Server


class App:
    def __init__(self, root):
        # Queue to receive messages from M.A.R.K.
        self._queue = queue.Queue()

        self._root = root
        self._root.columnconfigure(0, weight=1)

        # Connection status
        self._status_frame = Frame(self._root)
        self._status_frame.grid(row=0, column=0)
        self._status_fixed_label = Label(self._status_frame, text="Status: ", font="Roboto 14 bold")
        self._status_fixed_label.grid(row=0, column=0)
        self._status_label = Label(self._status_frame, text="Offline", fg="red", font="Roboto 14 bold")
        self._status_label.grid(row=0, column=1)

        # Camera feed
        self._camera_label = Label(self._root, text="Camera Feed", font="Roboto 14 bold")
        self._camera_label.grid(row=1, column=0, sticky="w", padx=250)
        self._camera_feed = Canvas(self._root, width=500, height=450)
        self._camera_feed.grid(row=2, column=0, sticky="w", padx=50, pady=10)
        # Initialize with a placeholder image while we wait to receive images from M.A.R.K.
        # We need to do this double assignment to prevent the image to be garbage collected
        # See: https://stackoverflow.com/questions/26479728/tkinter-canvas-image-not-displaying
        self._root.placeholder_image = placeholder_image = ImageTk.PhotoImage(file="img/placeholder.png")
        self._camera_feed_image = self._camera_feed.create_image(0, 0, anchor="nw", image=placeholder_image)

        # Start the server
        self._server = Server(host="localhost", port=1060, message_queue=self._queue)
        # We set the server as a daemon so that it can be killed when the app is closed
        self._server.daemon = True
        self._server.start()

        # Update the UI based on events from M.A.R.K.
        self._update()

    def close(self):
        self._server.close()
        self._root.destroy()

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
