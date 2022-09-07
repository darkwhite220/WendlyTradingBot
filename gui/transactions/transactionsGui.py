from tkinter import *
from tkinter import ttk


class TransactionGui(ttk.Frame):
    """Display Transactions (Frame) layout"""

    NEWS = "news"

    def __init__(self, parent):
        super().__init__(parent, padding=5)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        ttk.Label(
            self,
            text="(Future update) Imagine a very good design and green charts all over bcs you are The Best "
            "Trader :)",
            justify="center",
        ).grid()

        # Bored? https://www.youtube.com/watch?v=dQw4w9WgXcQ :)
