"""Main app for controlling M.A.R.K. and recording data."""
import logging
import queue
import sys

# For buttons to render properly in MacOS, we need to import `ttk`
# See: https://stackoverflow.com/q/59006014
from tkinter import Frame, Label, Tk, messagebox, ttk
from typing import Any

from server import MESSAGE_TYPE, Server


class App:
    def __init__(self, root):
        # Queue to receive messages from M.A.R.K.
        self._queue = queue.Queue()

        self._root = root
        self._frame = Frame(root)
        self._frame.pack()

        self._status_fixed_label = Label(self._frame, text="Status: ", font="Roboto 14 bold")
        self._status_fixed_label.pack(side="left")

        self._status_label = Label(self._frame, text="Offline", fg="red", font="Roboto 14 bold")
        self._status_label.pack(side="left")

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
