from dataclasses import dataclass, field


@dataclass
class Transaction:
    """Hold transaction datas to be saved"""

    time: str = field(init=False)
    position: str = field(init=False)
    txn_type: str = field(init=False)
    status: str = field(init=False)
    name: str = field(init=False)
    address: str = field(init=False)
    price: str = field(init=False)
    slippage: str = field(init=False)
    pay: str = field(init=False)
    quantity: str = field(init=False)
    profit: str = field(init=False)
    profit_percentage: str = field(init=False)
    txn_path: str = field(init=False)
    gas_price: str = field(init=False)
    txn_hash: str = field(init=False)

    def __init__(self):
        self.time = ""
        self.position = "/"
        self.txn_type = ""
        self.status = ""
        self.name = ""
        self.address = ""
        self.price = "0"
        self.slippage = "0"
        self.pay = "0"
        self.quantity = "0"
        self.profit = "0"
        self.profit_percentage = "0"
        self.txn_path = "/"
        self.gas_price = ""
        self.txn_hash = ""
