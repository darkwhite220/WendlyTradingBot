from tkinter import *
from tkinter import ttk

from helpers.settings import Settings


class SettingsGui(Toplevel):
    """Display Settings (TopLevel) layout

    Visibility: Withdrawal/Deiconify (with grab/release focus)
    """

    def __init__(self, parent: Tk, width, height):
        super().__init__(parent)
        self.resizable(False, False)
        self.title("Settings")
        # Center Settings window (w/ theme size = 614x401 w/out 597x307)
        x = (width - 600) / 2
        y = (height - 350) / 2
        self.geometry("+%d+%d" % (x, y))
        self.withdraw()  # Remove on first launch
        self.iconbitmap("./data/logo.ico")

        self.root_settings = ttk.LabelFrame(self, text="Settings")
        self.root_settings.grid(
            row=0,
            column=0,
            ipady=5,
            ipadx=10,
            pady=10,
            padx=10,
            columnspan=8,
            sticky="news",
        )
        self.root_settings.rowconfigure(0, weight=0)
        self.root_settings.columnconfigure(0, weight=0)
        self.root_settings.columnconfigure(1, weight=1, minsize=300)

        # Labels
        ttk.Label(self.root_settings, text="Wallet Address").grid(row=0, column=0, padx=10)
        ttk.Label(self.root_settings, text="Private Key").grid(row=1, column=0, padx=10)
        ttk.Label(self.root_settings, text="BSC Node").grid(row=2, column=0, padx=10)
        ttk.Label(self.root_settings, text="Max Gas Amount").grid(row=3, column=0, padx=10)
        ttk.Label(self.root_settings, text="Gas Price").grid(row=4, column=0, padx=10)
        ttk.Label(self.root_settings, text="Revert Transaction Time").grid(row=5, column=0, padx=10)
        ttk.Label(self.root_settings, text="Max Fail Transactions").grid(row=6, column=0, padx=10)

        # User input
        self.ent_wallet_address = ttk.Entry(self.root_settings, justify="center")
        self.ent_wallet_address.grid(row=0, column=1, padx=10, pady=5, sticky="we")
        self.ent_private_key = ttk.Entry(self.root_settings, justify="center")
        self.ent_private_key.grid(row=1, column=1, padx=10, pady=5, sticky="we")
        self.ent_bsc_node = ttk.Entry(self.root_settings, justify="center")
        self.ent_bsc_node.grid(row=2, column=1, padx=10, pady=5, sticky="we")
        self.ent_max_gas = ttk.Spinbox(
            self.root_settings,
            justify="center",
            from_=400000,
            to=2000000,
            increment=100000,
        )
        self.ent_max_gas.grid(row=3, column=1, padx=10, pady=5, sticky="we")
        self.ent_gas_price = ttk.Spinbox(self.root_settings, justify="center", from_=5.0, to=200.0, increment=5.0)
        self.ent_gas_price.grid(row=4, column=1, padx=10, pady=5, sticky="we")
        self.ent_revert_transaction = ttk.Spinbox(self.root_settings, justify="center", from_=5, to=60, increment=5)
        self.ent_revert_transaction.grid(row=5, column=1, padx=10, pady=5, sticky="we")
        self.ent_retry_count = ttk.Spinbox(self.root_settings, justify="center", from_=3, to=100, increment=1)
        self.ent_retry_count.grid(row=6, column=1, padx=10, pady=5, sticky="we")

        self.settings = self.get_settings()
        self.init_vars()
        self.set_vars()

        ttk.Button(self, text="Cancel", command=self.remove).grid(
            row=1, column=6, padx=10, pady=(0, 10), ipady=5, sticky="we"
        )
        ttk.Button(self, text="Save", command=self.save_settings).grid(
            row=1, column=7, padx=10, pady=(0, 10), ipady=5, sticky="we"
        )
        self.wm_protocol("WM_DELETE_WINDOW", self.remove)

    def set_state(self, state: str):
        """Disable fields if Trading is running"""
        self.ent_wallet_address.config(state=state)
        self.ent_private_key.config(state=state)
        self.ent_bsc_node.config(state=state)

    def init_vars(self):
        self.wallet_var = StringVar(value=self.settings.wallet)
        self.private_var = StringVar(value=self.settings.private_key)
        self.node_var = StringVar(value=self.settings.bcs_node)
        self.gas_amount_var = IntVar(value=self.settings.gas_amount)
        self.gas_price_var = DoubleVar(value=self.settings.gas_price)
        self.revert_time_var = IntVar(value=self.settings.revert_time)
        self.retry_max_var = IntVar(value=self.settings.max_fail_attempts)

    def set_vars(self):
        self.ent_wallet_address.config(textvariable=self.wallet_var)
        self.ent_private_key.config(textvariable=self.private_var)
        self.ent_bsc_node.config(textvariable=self.node_var)
        self.ent_max_gas.config(textvariable=self.gas_amount_var)
        self.ent_gas_price.config(textvariable=self.gas_price_var)
        self.ent_revert_transaction.config(textvariable=self.revert_time_var)
        self.ent_retry_count.config(textvariable=self.retry_max_var)

    def get_settings(self) -> Settings:
        pass

    def save_settings(self):
        pass

    def remove(self):
        if self.state() != "withdrawn":
            self.settings = self.get_settings()  # Reset vars if didn't save
            self.init_vars()
            self.set_vars()
            self.withdraw()
        self.grab_release()
