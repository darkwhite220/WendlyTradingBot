import sys
import tkinter.scrolledtext as st
import tkinter.ttk as ttk
from datetime import time
from tkinter.ttk import Frame


# TODO add timestamp
class PrintLogging:
    """Take root frame to place a ScrolledText and print logs into it

    Args: frame (parent)

    Return: None
    """

    def __init__(self, root: Frame):
        self.lbl_frm_logging = ttk.LabelFrame(root, text="Logging")
        self.lbl_frm_logging.grid(row=0, column=4, pady=5, padx=5, sticky="news")
        self.lbl_frm_logging.rowconfigure(0, weight=1)
        self.lbl_frm_logging.columnconfigure(0, weight=1)

        self.scrolled_text = st.ScrolledText(self.lbl_frm_logging, wrap="word", state="disabled", width=1, height=1)
        self.scrolled_text.grid(row=0, column=0, padx=5, pady=5, sticky="news")
        sys.stdout = self

    def write(self, text):
        self.scrolled_text.configure(state="normal")
        self.scrolled_text.insert(index="end", chars=text)
        self.scrolled_text.see(index="end")
        self.scrolled_text.configure(state="disabled")

    def flush(self):
        pass
