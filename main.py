from tkinter import *

from gui.settings.settingsCommands import SettingsCommands
from gui.trading.tradingCommands import TradingCommands
from gui.transactions.transactionsGui import TransactionGui

# import sv_ttk  # Uncomment sv_ttk line 26 to use the theme (make the app lag when resizing)


class WendlyGui(Tk):
    NEWS = "news"

    def __init__(self):
        super().__init__()
        self.root_config()
        self.create_menu()
        self.frm_trading = TradingCommands(self)
        self.frm_transactions = TransactionGui(self)
        self.top_lvl_settings = SettingsCommands(self, self.screen_width, self.screen_height)
        self.top_lvl_settings.bind("<Unmap>", self.update_trading_settings)
        self.display_menu_trading()

    def root_config(self):
        """Set window params (title, resize, geometry)"""

        # sv_ttk.set_theme("dark")  # light or dark
        self.resizable(True, True)
        self.title("Wendly Trading Bot")
        self.iconbitmap("./data/logo.ico")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # Center window (w/ theme size = 1312x791 w/out 1300x565)
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        x = (self.screen_width - 1300) / 2
        y = (self.screen_height - 650) / 2
        self.geometry("1300x565+%d+%d" % (x, y))

    def create_menu(self):
        """Create menu (Trading - Settings - Transactions)"""
        menu = Menu(self)
        self.config(menu=menu)
        menu.add_command(label="Trading", command=self.display_menu_trading)
        menu.add_command(label="Settings", command=self.display_menu_settings)
        menu.add_command(label="Transactions", command=self.display_menu_transaction)

    def remove_frames(self):
        self.frm_trading.grid_remove()
        self.frm_transactions.grid_remove()
        self.top_lvl_settings.remove()

    @staticmethod
    def decorator_remove_frames(func):
        def wrapper(self):
            self.remove_frames()
            return func(self)

        return wrapper

    @decorator_remove_frames
    def display_menu_trading(self):
        self.frm_trading.set_settings(self.top_lvl_settings.settings)
        self.frm_trading.grid(column=0, row=0, sticky=self.NEWS)

    def display_menu_settings(self):
        self.top_lvl_settings.set_state(str(self.frm_trading.btn_start["state"]))
        self.top_lvl_settings.deiconify()
        self.top_lvl_settings.grab_set()

    @decorator_remove_frames
    def display_menu_transaction(self):
        self.frm_transactions.grid(column=0, row=0, sticky=self.NEWS)

    def update_trading_settings(self, _):
        self.frm_trading.set_settings(self.top_lvl_settings.settings)


if __name__ == "__main__":
    app: Tk = WendlyGui()
    app.mainloop()
