import json
import os
from tkinter import Tk

from gui.settings.settingsGui import SettingsGui
from helpers.settings import Settings


class SettingsCommands(SettingsGui):
    """Child of SettingsGui Class, Get & Save settings"""

    def __init__(self, parent: Tk, width: int, height: int):
        super().__init__(parent, width, height)

    def get_settings(self) -> Settings:
        """Get saved settings or default values

        param
           wallet: String

           private_key: String

           bcs_node: String

           gas_amount: Int

           gas_price: Double

           revert_time: Int

           max_fail_attempts: Int
        """

        try:
            with open(os.path.join(os.getcwd(), "./data/settings.json"), "r") as sFile:
                return Settings(**json.load(sFile))
        except (
            OSError,
            IOError,
            FileNotFoundError,
            json.decoder.JSONDecodeError,
        ) as ex:
            print("get_tokens fail", ex)
        return Settings()

    def save_settings(self):
        """Save settings (Enforcing min/default values) then withdraw & release focus

        param
           wallet: String

           private_key: String

           bcs_node: String

           gas_amount: Int

           gas_price: Double

           revert_time: Int

           max_fail_attempts: Int
        """

        try:
            temp_dict = {
                "wallet": self.wallet_var.get().strip(),
                "private_key": self.private_var.get().strip(),
                "bcs_node": (
                    "https://bsc-dataseed1.defibit.io"
                    if self.node_var.get().strip() == ""
                    else self.node_var.get().strip()
                ),
                "gas_amount": int(max(self.gas_amount_var.get(), 400000)),
                "gas_price": max(self.gas_price_var.get(), 5.0),
                "revert_time": int(max(self.revert_time_var.get(), 5)),
                "max_fail_attempts": int(max(self.retry_max_var.get(), 0)),
            }
            with open(os.path.join(os.getcwd(), "./data/settings.json"), "w") as sFile:
                json.dump(temp_dict, sFile, indent=4)
                print("Saved settings successfully.")
            self.settings = Settings(**temp_dict)  # Update
        except (OSError, IOError, Exception) as ex:
            print(ex)

        self.withdraw()
        self.grab_release()
