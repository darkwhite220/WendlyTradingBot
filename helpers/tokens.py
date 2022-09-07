import dataclasses
import json
from dataclasses import dataclass, field

from dacite import from_dict


@dataclass
class LimitTrade:
    sell_multiplier: list[str] = field(init=False)
    sell_quantity: list[str] = field(init=False)
    order_done: list[bool] = field(init=False)
    buy_at: str = field(init=False)
    pay_currency: str = field(init=False)
    pay_amount: str = field(init=False)
    repetition: int = field(init=False)
    unit_buy_price: str = field(init=False)
    qnt_bought: str = field(init=False)
    rep_done: int = field(init=False)

    def __init__(self):
        # Str not float for Decimals
        self.sell_multiplier = ["120.0", "105.0", "90.0", "0.0"]
        self.sell_quantity = ["80.0", "10.0", "100.0", "0.0"]
        self.order_done = [False, False, False, False]
        self.buy_at: str = "0.001"
        self.pay_currency: str = "BNB"
        self.pay_amount: str = "0.00001"
        self.repetition: int = 0
        self.unit_buy_price: str = "0"
        self.qnt_bought: str = "0"
        self.rep_done: int = 0


@dataclass
class Tokens:
    name: str = field(init=False)
    address: str = field(init=False)
    dex: str = field(init=False)
    slippage: str = field(init=False)
    buy_tax: str = field(init=False)
    sell_tax: str = field(init=False)
    limit_trade: LimitTrade = field(init=False)

    def __init__(self):
        self.name: str = "Empty"
        self.address: str = ""
        self.dex: str = "PancakeSwap v2"
        self.slippage: str = "5.0"
        self.buy_tax: str = "0.0"
        self.sell_tax: str = "0.0"
        self.limit_trade = LimitTrade()


class DataClassJsonEncoder(json.JSONEncoder):
    def default(self, o):
        return dataclasses.asdict(o)
