import os
from tkinter import *

from gui.trading.tradingGui import TradingGui
from helpers.settings import Settings
from helpers.tokens import *
from web.webLayer import WebLayer


class TradingCommands(TradingGui):
    """Handle TradingGui Class events"""

    def __init__(self, parent: Tk):
        self.previews_pos: int = -1
        super().__init__(parent)
        self.settings: Settings
        self.web_layer: WebLayer = None

    def get_tokens(self) -> list[Tokens]:
        """Return: list[Tokens] Saved in "./data/tokens.json" """
        temp_list: list[Tokens] = []
        try:
            with open(os.path.join(os.getcwd(), "./data/tokens.json"), "r") as sFile:
                temp_json = json.load(sFile)
                temp_list = [from_dict(Tokens, item) for item in temp_json]
                if len(temp_list) == 0:
                    temp_list.append(Tokens())
        except (
            OSError,
            IOError,
            FileNotFoundError,
            json.decoder.JSONDecodeError,
        ) as ex:
            print("Error (GetTokens):", ex)
            temp_list.append(Tokens())
        return temp_list

    def insert_tokens_in_tree_view(self):
        """Insert list[Tokens] in TreeView and focus position 0"""
        for i, item in enumerate(self.tokens_list):
            self.tv_tokens.insert("", "end", iid=str(i), values=(item.name,))
        self.tv_tokens.selection_set("0")
        self.tv_tokens.focus_set()
        self.tv_tokens.focus("0")

    def on_tree_view_selection_change(self, _):
        """On TreeView selection change:

        -Save entries of preview_position

        -Update entries to the new TreView selected token

        -Update previews_position
        """
        index: str = self.tv_tokens.focus()
        if index == "":
            return
        if self.previews_pos != -1:
            self.token_modification_check(self.previews_pos)
        index: int = int(index)
        self.update_vars(index)
        self.previews_pos = index

    def update_vars(self, index: int = 0):
        """Update Entries/SpinBox values, & change states if needed"""
        self.name_var.set(value=self.tokens_list[index].name)
        self.address_var.set(value=self.tokens_list[index].address)
        self.dex_var.set(value=self.tokens_list[index].dex)
        self.slippage_var.set(value=self.tokens_list[index].slippage)
        self.buy_tax_var.set(value=self.tokens_list[index].buy_tax)
        self.sell_tax_var.set(value=self.tokens_list[index].sell_tax)
        # Limit trade
        self.lmt_buy_price_var.set(value=self.tokens_list[index].limit_trade.buy_at)
        self.lmt_pay_amount_var.set(value=self.tokens_list[index].limit_trade.pay_amount)
        self.lmt_pay_currency_var.set(value=self.tokens_list[index].limit_trade.pay_currency)

        self.lmt_sell_p1_var.set(value=self.tokens_list[index].limit_trade.sell_multiplier[0])
        self.lmt_sell_pa1_var.set(value=self.tokens_list[index].limit_trade.sell_quantity[0])
        self.lmt_sell_p2_var.set(value=self.tokens_list[index].limit_trade.sell_multiplier[1])
        self.lmt_sell_pa2_var.set(value=self.tokens_list[index].limit_trade.sell_quantity[1])
        self.lmt_sell_l1_var.set(value=self.tokens_list[index].limit_trade.sell_multiplier[2])
        self.lmt_sell_la1_var.set(value=self.tokens_list[index].limit_trade.sell_quantity[2])
        self.lmt_sell_l2_var.set(value=self.tokens_list[index].limit_trade.sell_multiplier[3])
        self.lmt_sell_la2_var.set(value=self.tokens_list[index].limit_trade.sell_quantity[3])

        self.update_state(index)

    def update_state(self, index: int):
        """Disable fields after we buy or sell & update repetition filed"""
        self.lmt_repetition_var.set(value=self.tokens_list[index].limit_trade.repetition)

        # Trading active
        if (self.web_layer is not None and not self.web_layer.stop) or self.tokens_list[
            index
        ].limit_trade.qnt_bought != "0":
            self.ent_token_address.config(state="disabled")
            self.cBox_dex.config(state="disabled")
        else:
            self.ent_token_address.config(state="normal")
            self.cBox_dex.config(state="normal")

        # Bought
        if self.tokens_list[index].limit_trade.qnt_bought != "0":
            self.ent_limit_buy_price.config(state="disabled")
            self.ent_limit_pay_amount.config(state="disabled")
            self.cBox_pay_currency.config(state="disabled")
        else:
            self.ent_limit_buy_price.config(state="normal")
            self.ent_limit_pay_amount.config(state="normal")
            self.cBox_pay_currency.config(state="normal")

        # Sold
        if self.tokens_list[index].limit_trade.order_done[0]:
            self.spnBox_limit_sell_p1.config(state="disabled")
            self.spnBox_limit_sell_pa1.config(state="disabled")
        else:
            self.spnBox_limit_sell_p1.config(state="normal")
            self.spnBox_limit_sell_pa1.config(state="normal")

        if self.tokens_list[index].limit_trade.order_done[1]:
            self.spnBox_limit_sell_p2.config(state="disabled")
            self.spnBox_limit_sell_pa2.config(state="disabled")
        else:
            self.spnBox_limit_sell_p2.config(state="normal")
            self.spnBox_limit_sell_pa2.config(state="normal")

        if self.tokens_list[index].limit_trade.order_done[2]:
            self.spnBox_limit_sell_l1.config(state="disabled")
            self.spnBox_limit_sell_la1.config(state="disabled")
        else:
            self.spnBox_limit_sell_l1.config(state="normal")
            self.spnBox_limit_sell_la1.config(state="normal")

        if self.tokens_list[index].limit_trade.order_done[3]:
            self.spnBox_limit_sell_l2.config(state="disabled")
            self.spnBox_limit_sell_la2.config(state="disabled")
        else:
            self.spnBox_limit_sell_l2.config(state="normal")
            self.spnBox_limit_sell_la2.config(state="normal")

    def add_token(self):
        """Add new Token to current list[Tokens], Position: last"""
        self.tokens_list.append(Tokens())
        self.update_tree_view_after_add()

    def update_tree_view_after_add(self):
        pos = str(len(self.tokens_list) - 1)
        self.tv_tokens.insert("", "end", iid=pos, values=(self.tokens_list[-1].name,))
        self.tv_tokens.selection_set(pos)
        self.tv_tokens.focus_set()
        self.tv_tokens.focus(pos)

    def token_modification_check(self, index: int):
        """Save entries vars (Enforcing min/max/default values) to list & change TreeView item name if needed"""
        self.tokens_list[index].name = self.name_var.get().strip() or "Empty"
        self.tokens_list[index].address = self.address_var.get().strip()
        self.tokens_list[index].dex = self.dex_var.get().strip() or "PancakeSwap v2"
        self.tokens_list[index].slippage = str(max(self.slippage_var.get(), 1.0))
        self.tokens_list[index].buy_tax = str(max(self.buy_tax_var.get(), 0.0))
        self.tokens_list[index].sell_tax = str(max(self.sell_tax_var.get(), 0.0))
        self.tokens_list[index].limit_trade.buy_at = self.lmt_buy_price_var.get()
        self.tokens_list[index].limit_trade.pay_amount = self.lmt_pay_amount_var.get()
        self.tokens_list[index].limit_trade.pay_currency = self.lmt_pay_currency_var.get().strip() or "BNB"
        self.tokens_list[index].limit_trade.repetition = self.lmt_repetition_var.get()

        self.tokens_list[index].limit_trade.sell_multiplier[0] = str(max(self.lmt_sell_p1_var.get(), 100.01))
        self.tokens_list[index].limit_trade.sell_multiplier[1] = str(max(self.lmt_sell_p2_var.get(), 100.01))
        self.tokens_list[index].limit_trade.sell_multiplier[2] = str(min(self.lmt_sell_l1_var.get(), 99.99))
        self.tokens_list[index].limit_trade.sell_multiplier[3] = str(min(self.lmt_sell_l2_var.get(), 99.99))

        self.tokens_list[index].limit_trade.sell_quantity[0] = str(min(self.lmt_sell_pa1_var.get(), 100.00))
        self.tokens_list[index].limit_trade.sell_quantity[1] = str(min(self.lmt_sell_pa2_var.get(), 100.00))
        self.tokens_list[index].limit_trade.sell_quantity[2] = str(min(self.lmt_sell_la1_var.get(), 100.00))
        self.tokens_list[index].limit_trade.sell_quantity[3] = str(min(self.lmt_sell_la2_var.get(), 100.00))

        self.tv_tokens.item(str(index), values=(self.tokens_list[index].name,))

    def delete_token(self):  # Todo popup
        """
        -Delete selected token form current list[Tokens]

        -Delete all TreeView items

        -Insert the new list[Tokens] in TreeView

        Reason: get the correct index or else TreeView & list indexes won't match
        """

        index: str = self.tv_tokens.focus()
        if index == "":
            return
        self.previews_pos = -1
        self.tokens_list.pop(int(index))  # remove from list
        for i in self.tv_tokens.get_children():  # reset tree view
            self.tv_tokens.delete(i)
        if len(self.tokens_list) == 0:
            self.add_token()
        else:
            self.insert_tokens_in_tree_view()

    def save_tokens(self):
        """Save & Send Tokes list to Trading"""
        self.token_modification_check(int(self.tv_tokens.focus()))
        try:
            with open(os.path.join(os.getcwd(), "./data/tokens.json"), "w") as sFile:
                json.dump(self.tokens_list, sFile, indent=4, cls=DataClassJsonEncoder)
                print("Saved tokens successfully.")

            self.update_thread_args()
        except (OSError, IOError) as ex:
            print("Error(Save tokens):", ex)

    def pause_bot(self):
        """Stop Trading Thread & update GUI"""
        self.web_layer.stop_thread()
        self.btn_pause.config(state="disabled")
        self.check_thread_status()

    def check_thread_status(self):
        if self.web_layer.is_alive():
            print("Please wait while finishing pending work . . .")
            self.after(1000, self.check_thread_status)
        else:
            self.fields_state_switcher()

    def start_bot(self):
        """Start Trading Thread & update GUI"""
        self.web_layer = WebLayer(self.tokens_list, self.settings)
        self.btn_pause.config(state="normal")
        self.fields_state_switcher()
        self.update_GUI()

    def fields_state_switcher(self):
        state = "normal" if self.web_layer.stop else "disabled"

        self.ent_token_name.config(state=state)
        self.cBox_pay_currency.config(state=state)
        self.btn_add_token.config(state=state)
        self.btn_delete_token.config(state=state)
        self.btn_start.config(state=state)

    def update_GUI(self):
        """Update GUI after txn buy/sell"""
        if not self.web_layer.stop:
            self.after(3000, self.update_GUI)
        else:
            self.pause_bot()
        self.update_state(int(self.tv_tokens.focus()))

    def set_settings(self, settings: Settings):
        """Save & Send Settings to Trading"""
        self.settings = settings
        self.update_thread_args()

    def update_thread_args(self):
        """Update settings & list[Tokens] values while Trading Thread is alive"""
        if self.web_layer is not None:
            self.web_layer.set_settings(self.settings)
            self.web_layer.set_tokens(self.tokens_list)
