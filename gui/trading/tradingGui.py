from tkinter import *
from tkinter import ttk

from helpers.printLogger import PrintLogging
from helpers.tokens import *


class TradingGui(ttk.Frame):
    """Display Trading (Frame) layout

    Separated to 3 frames

        Frame 1: TreeView to display tokens list & buttons (Add, Delete, Save, Pause & Start)

        Frame 2: Separated to 2 frames

            Frame 2.1: Token details (Name, Address, Dex, Slippage, Buy/Sell tax)

            Frame 2.2: NoteBook for trading strategies (Limit trade, Trailing Stop, Buy The Dip),
            Each with their entries.

        Frame 3: ScrolledText, Display logs
    """

    NEWS = "news"

    def __init__(self, parent: Tk):
        super().__init__(parent, padding=5)
        # self.grid(row=0, column=0, sticky=self.NEWS)  # placed in main.py
        self.rowconfigure(0, weight=1, minsize=500)
        self.columnconfigure(0, weight=0, minsize=240)  # token_list_frame
        self.columnconfigure(1, weight=0, minsize=5)  # separator
        self.columnconfigure(2, weight=0, minsize=500)  # token_details_and_strategies_frame
        self.columnconfigure(3, weight=0, minsize=5)  # separator
        self.columnconfigure(4, weight=1, minsize=500)  # PrintLogging

        self.tokens_list = self.get_tokens()
        self.init_vars()

        self.token_list_frame()
        self.token_details_and_strategies_frame()

        PrintLogging(self)

    def token_list_frame(self):
        self.frm_tokens = ttk.Frame(self)
        self.frm_tokens.grid(row=0, column=0, sticky=self.NEWS)
        self.frm_tokens.rowconfigure(0, weight=1)
        self.frm_tokens.rowconfigure(1, weight=0)
        self.frm_tokens.rowconfigure(2, weight=0, minsize=80)
        self.frm_tokens.columnconfigure([0, 1, 2, 3, 4, 5], weight=0, minsize=40)

        # Tokens TreeView
        self.tv_tokens = ttk.Treeview(self.frm_tokens, selectmode="browse", columns="tokens", show="headings")
        self.tv_tokens.heading("tokens", text="Tokens List")
        self.tv_tokens.grid(row=0, column=0, padx=5, pady=5, sticky=self.NEWS, columnspan=6)
        # Scrollbar for TreeView
        self.vsb_view = ttk.Scrollbar(self.tv_tokens, orient=VERTICAL, command=self.tv_tokens.yview)
        self.vsb_view.pack(side=RIGHT, fill=Y, pady=(35, 10), padx=1)
        self.tv_tokens.configure(yscrollcommand=self.vsb_view.set)
        # Fill TV with datas
        self.insert_tokens_in_tree_view()
        self.tv_tokens.bind("<<TreeviewSelect>>", self.on_tree_view_selection_change)

        # Buttons Add/Save/Delete/Pause/Start
        self.btn_add_token = ttk.Button(self.frm_tokens, text="Add", command=self.add_token)
        self.btn_add_token.grid(row=1, column=0, sticky="ew", pady=5, padx=5, columnspan=2)
        self.btn_save_token = ttk.Button(self.frm_tokens, text="Save", command=self.save_tokens)
        self.btn_save_token.grid(row=1, column=2, sticky="ew", pady=5, padx=5, columnspan=2)
        self.btn_delete_token = ttk.Button(self.frm_tokens, text="Delete", command=self.delete_token)
        self.btn_delete_token.grid(row=1, column=4, sticky="ew", pady=5, padx=5, columnspan=2)
        self.btn_pause = ttk.Button(self.frm_tokens, text="Pause", command=self.pause_bot, state="disabled")
        self.btn_pause.grid(row=2, column=0, pady=5, padx=5, sticky=self.NEWS, columnspan=3)
        self.btn_start = ttk.Button(self.frm_tokens, text="Start", command=self.start_bot)
        self.btn_start.grid(row=2, column=3, pady=5, padx=5, sticky=self.NEWS, columnspan=3)

    def token_details_and_strategies_frame(self):
        self.frm_details = ttk.Frame(self)
        self.frm_details.grid(row=0, column=2, sticky=self.NEWS)
        self.frm_details.rowconfigure(0, weight=0)
        self.frm_details.rowconfigure(1, weight=0)
        self.frm_details.columnconfigure(0, weight=0, minsize=500)

        self.token_detail_frame()
        self.token_trade_strategies_frame()

    def token_detail_frame(self):
        self.lbl_frm_token_detail = ttk.LabelFrame(self.frm_details, text="Token Details")
        self.lbl_frm_token_detail.grid(row=0, column=0, pady=5, padx=5, ipady=5, sticky=self.NEWS)
        self.lbl_frm_token_detail.rowconfigure(0, weight=0)
        self.lbl_frm_token_detail.columnconfigure(0, weight=0)
        self.lbl_frm_token_detail.columnconfigure([0, 1], weight=1)

        # Labels
        ttk.Label(self.lbl_frm_token_detail, text="Token Name").grid(row=0, column=0, padx=8, sticky="w")
        ttk.Label(self.lbl_frm_token_detail, text="Token Address").grid(row=1, column=0, padx=8, sticky="w")
        ttk.Label(self.lbl_frm_token_detail, text="DEX").grid(row=2, column=0, padx=8, sticky="w")
        ttk.Label(self.lbl_frm_token_detail, text="Slippage").grid(row=3, column=0, padx=8, sticky="w")
        ttk.Label(self.lbl_frm_token_detail, text="Taxes (Buy/Sell)").grid(row=4, column=0, padx=8, sticky="w")

        # User input
        self.ent_token_name = ttk.Entry(self.lbl_frm_token_detail, justify="center", textvariable=self.name_var)
        self.ent_token_name.grid(row=0, column=1, padx=8, pady=2, sticky="we", columnspan=2)
        self.ent_token_address = ttk.Entry(self.lbl_frm_token_detail, justify="center", textvariable=self.address_var)
        self.ent_token_address.grid(row=1, column=1, padx=8, pady=2, sticky="we", columnspan=2)
        self.cBox_dex = ttk.Combobox(
            self.lbl_frm_token_detail,
            values=["PancakeSwap v2", "BabySwap", "BiSwap", "ApeSwap", "BustaSwap"],
            textvariable=self.dex_var,
            justify="center",
        )
        self.cBox_dex.grid(row=2, column=1, padx=8, pady=2, sticky="we", columnspan=2)
        self.ent_slippage = ttk.Spinbox(
            self.lbl_frm_token_detail,
            from_=1.0,
            to=100.0,
            increment=1.0,
            justify="center",
            textvariable=self.slippage_var,
        )
        self.ent_slippage.grid(row=3, column=1, padx=8, pady=5, sticky="we", columnspan=2)
        self.ent_buy_tax = ttk.Spinbox(
            self.lbl_frm_token_detail,
            from_=1.0,
            to=100.0,
            increment=1.0,
            justify="center",
            textvariable=self.buy_tax_var,
        )
        self.ent_buy_tax.grid(row=4, column=1, padx=8, pady=5, sticky="we")
        self.ent_sell_tax = ttk.Spinbox(
            self.lbl_frm_token_detail,
            from_=1.0,
            to=100.0,
            increment=1.0,
            justify="center",
            textvariable=self.sell_tax_var,
        )
        self.ent_sell_tax.grid(row=4, column=2, padx=8, pady=5, sticky="we")

    def token_trade_strategies_frame(self):
        self.ntbk_trade_strategies = ttk.Notebook(self.frm_details)
        # Notebook trade strategies frames
        self.frm_limit_trade = ttk.Frame(self.ntbk_trade_strategies)
        self.frm_limit_trade.grid(row=0, column=0)
        self.frm_trailing_stop_trade = ttk.Frame(self.ntbk_trade_strategies)
        self.frm_trailing_stop_trade.grid(row=0, column=0)
        self.frm_buy_dip_trade = ttk.Frame(self.ntbk_trade_strategies)
        self.frm_buy_dip_trade.grid(row=0, column=0)

        self.ntbk_trade_strategies.add(self.frm_limit_trade, text="Limit Trade")
        self.ntbk_trade_strategies.add(self.frm_trailing_stop_trade, text="Trailing Stop")
        self.ntbk_trade_strategies.add(self.frm_buy_dip_trade, text="Buy The Dip")
        self.ntbk_trade_strategies.grid(row=1, column=0, pady=5, padx=5, sticky=self.NEWS)

        self.str_limit_trade()
        self.str_trailing_stop()
        self.str_buy_dip()

    def str_limit_trade(self):
        self.frm_limit_trade.configure(padding=(0, 5, 0, 5))
        self.frm_limit_trade.rowconfigure(0, weight=0)
        self.frm_limit_trade.columnconfigure(0, weight=0)
        self.frm_limit_trade.columnconfigure(1, weight=1)

        # Buy Part, Labels
        ttk.Label(self.frm_limit_trade, text="Buy under this price ($)").grid(row=0, column=0, padx=8, sticky="w")
        ttk.Label(self.frm_limit_trade, text="Pay currency").grid(row=1, column=0, padx=8, sticky="w")
        ttk.Label(self.frm_limit_trade, text="Pay amount").grid(row=2, column=0, padx=8, sticky="w")
        ttk.Label(self.frm_limit_trade, text="Repetition").grid(row=3, column=0, padx=8, sticky="w")
        # User input
        self.ent_limit_buy_price = ttk.Entry(
            self.frm_limit_trade, justify="center", textvariable=self.lmt_buy_price_var
        )
        self.ent_limit_buy_price.grid(row=0, column=1, padx=8, pady=2, sticky="we")
        self.cBox_pay_currency = ttk.Combobox(
            self.frm_limit_trade,
            values=["BNB", "USDT", "BUSD"],
            textvariable=self.lmt_pay_currency_var,
            justify="center",
        )
        self.cBox_pay_currency.grid(row=1, column=1, padx=8, pady=2, sticky="we")
        self.ent_limit_pay_amount = ttk.Entry(
            self.frm_limit_trade, justify="center", textvariable=self.lmt_pay_amount_var
        )
        self.ent_limit_pay_amount.grid(row=2, column=1, padx=8, pady=2, sticky="we")
        self.spnBox_repetition = ttk.Spinbox(
            self.frm_limit_trade,
            from_=0,
            to=10,
            textvariable=self.lmt_repetition_var,
            justify="center",
        )
        self.spnBox_repetition.grid(row=3, column=1, padx=8, pady=2, sticky="we")

        # Sell On Profit Part
        ttk.Separator(self.frm_limit_trade).grid(row=4, column=0, columnspan=2, padx=40, pady=10, sticky="we")
        # Labels
        ttk.Label(self.frm_limit_trade, text="Sell multiplier on profit (%)").grid(row=5, column=0, padx=8, sticky="w")
        ttk.Label(self.frm_limit_trade, text="Sell amount (%)").grid(row=6, column=0, padx=8, sticky="w")
        ttk.Label(self.frm_limit_trade, text="Sell multiplier on profit (%)").grid(row=7, column=0, padx=8, sticky="w")
        ttk.Label(self.frm_limit_trade, text="Sell amount (%)").grid(row=8, column=0, padx=8, sticky="w")
        # User input
        self.spnBox_limit_sell_p1 = ttk.Spinbox(
            self.frm_limit_trade,
            from_=101,
            to=500,
            increment=10.0,
            justify="center",
            textvariable=self.lmt_sell_p1_var,
        )
        self.spnBox_limit_sell_p1.grid(row=5, column=1, padx=8, pady=2, sticky="we")
        self.spnBox_limit_sell_pa1 = ttk.Spinbox(
            self.frm_limit_trade,
            from_=5.0,
            to=100.0,
            increment=5.0,
            justify="center",
            textvariable=self.lmt_sell_pa1_var,
        )
        self.spnBox_limit_sell_pa1.grid(row=6, column=1, padx=8, pady=2, sticky="we")
        self.spnBox_limit_sell_p2 = ttk.Spinbox(
            self.frm_limit_trade,
            from_=101.0,
            to=500.0,
            increment=10.0,
            justify="center",
            textvariable=self.lmt_sell_p2_var,
        )
        self.spnBox_limit_sell_p2.grid(row=7, column=1, padx=8, pady=2, sticky="we")
        self.spnBox_limit_sell_pa2 = ttk.Spinbox(
            self.frm_limit_trade,
            from_=5.0,
            to=100.0,
            increment=5.0,
            justify="center",
            textvariable=self.lmt_sell_pa2_var,
        )
        self.spnBox_limit_sell_pa2.grid(row=8, column=1, padx=8, pady=2, sticky="we")

        # Sell On Loss Part
        ttk.Separator(self.frm_limit_trade).grid(row=9, column=0, columnspan=2, padx=40, pady=10, sticky="we")
        # Labels
        ttk.Label(self.frm_limit_trade, text="Sell multiplier on loss (%)").grid(row=10, column=0, padx=8, sticky="w")
        ttk.Label(self.frm_limit_trade, text="Sell amount (%)").grid(row=11, column=0, padx=8, sticky="w")
        ttk.Label(self.frm_limit_trade, text="Sell multiplier on loss (%)").grid(row=12, column=0, padx=8, sticky="w")
        ttk.Label(self.frm_limit_trade, text="Sell amount (%)").grid(row=13, column=0, padx=8, sticky="w")
        # User input
        self.spnBox_limit_sell_l1 = ttk.Spinbox(
            self.frm_limit_trade,
            from_=1.0,
            to=99.0,
            increment=10.0,
            justify="center",
            textvariable=self.lmt_sell_l1_var,
        )
        self.spnBox_limit_sell_l1.grid(row=10, column=1, padx=8, pady=2, sticky="we")
        self.spnBox_limit_sell_la1 = ttk.Spinbox(
            self.frm_limit_trade,
            from_=5.0,
            to=100.0,
            increment=5.0,
            justify="center",
            textvariable=self.lmt_sell_la1_var,
        )
        self.spnBox_limit_sell_la1.grid(row=11, column=1, padx=8, pady=2, sticky="we")
        self.spnBox_limit_sell_l2 = ttk.Spinbox(
            self.frm_limit_trade,
            from_=1.0,
            to=99.0,
            increment=10.0,
            justify="center",
            textvariable=self.lmt_sell_l2_var,
        )
        self.spnBox_limit_sell_l2.grid(row=12, column=1, padx=8, pady=2, sticky="we")
        self.spnBox_limit_sell_la2 = ttk.Spinbox(
            self.frm_limit_trade,
            from_=5.0,
            to=100.0,
            increment=5.0,
            justify="center",
            textvariable=self.lmt_sell_la2_var,
        )
        self.spnBox_limit_sell_la2.grid(row=13, column=1, padx=8, pady=2, sticky="we")

    def str_trailing_stop(self):
        self.frm_trailing_stop_trade.configure(padding=(0, 5, 0, 5))
        ttk.Label(
            self.frm_trailing_stop_trade,
            text="This feature will be implemented in future updates.",
        ).grid(row=0, column=0, pady=6, padx=8, sticky="we")

    def str_buy_dip(self):
        self.frm_buy_dip_trade.configure(padding=(0, 5, 0, 5))
        ttk.Label(
            self.frm_buy_dip_trade,
            text="This feature will be implemented in future updates.",
        ).grid(row=0, column=0, pady=6, padx=8, sticky="we")

    def insert_tokens_in_tree_view(self):
        pass

    def init_vars(self):
        # Details
        self.name_var: StringVar = StringVar()
        self.address_var: StringVar = StringVar()
        self.dex_var: StringVar = StringVar()
        self.slippage_var: DoubleVar = DoubleVar()
        self.buy_tax_var: DoubleVar = DoubleVar()
        self.sell_tax_var: DoubleVar = DoubleVar()
        # Limit trade
        self.lmt_buy_price_var: StringVar = StringVar()
        self.lmt_pay_amount_var: StringVar = StringVar()
        self.lmt_pay_currency_var: StringVar = StringVar()
        self.lmt_repetition_var: IntVar = IntVar()
        self.lmt_sell_p1_var: DoubleVar = DoubleVar()
        self.lmt_sell_pa1_var: DoubleVar = DoubleVar()
        self.lmt_sell_p2_var: DoubleVar = DoubleVar()
        self.lmt_sell_pa2_var: DoubleVar = DoubleVar()
        self.lmt_sell_l1_var: DoubleVar = DoubleVar()
        self.lmt_sell_la1_var: DoubleVar = DoubleVar()
        self.lmt_sell_l2_var: DoubleVar = DoubleVar()
        self.lmt_sell_la2_var: DoubleVar = DoubleVar()

    def get_tokens(self) -> list[Tokens]:
        pass

    def on_tree_view_selection_change(self, _):
        pass

    def add_token(self):
        pass

    def save_tokens(self):
        pass

    def delete_token(self):
        pass

    def pause_bot(self):
        pass

    def start_bot(self):
        pass
