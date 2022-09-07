import decimal

from helpers.settings import Settings
from helpers.tokens import Tokens
from helpers.utils import *

decimal.setcontext(decimal.Context(prec=60, rounding=decimal.ROUND_DOWN))


class TokenData:
    """Fetch Token Data:

    -Allowance -Symbol -Decimals -Supply -TradingPath -Token Balance
    """

    def __init__(self, web3, token: Tokens, settings: Settings, dex: dict, bnb_price: Decimal):
        self.w3 = web3
        self.token = token
        self.settings = settings
        self.standard_abi: dict = standard_abi
        self.dex = dex
        self.LP_abi: dict = LP_abi
        self.price_in_usd: float = 0
        self.price_in_bnb: float = 0
        factory_address: str = Web3.toChecksumAddress(self.dex["FACTORY"])
        self.router_address: str = Web3.toChecksumAddress(self.dex["ROUTER"])
        self.token_contract: contract = self.w3.eth.contract(address=self.token.address, abi=self.standard_abi)
        self.factory_contract: contract = self.w3.eth.contract(address=factory_address, abi=self.dex["FACTORY_ABI"])
        self.router_contract: contract = self.w3.eth.contract(address=self.router_address, abi=self.dex["ROUTER_ABI"])
        self.to_print: str = ""
        self.bnb_price = bnb_price
        self.buy_path_symbol: str = ""
        self.error: bool = False
        self.counter_symbol: str = ""

        self.allowance = get_allowance(self.token_contract, self.settings.wallet, self.router_address)

        self.fetch_token_data()
        self.find_trading_pair()
        self.find_transaction_path()
        self.fetch_token_balance()

    # @timer
    def fetch_token_data(self):
        """Token symbol, decimals, & supply"""
        self.symbol: str = self.token_contract.functions.symbol().call()
        self.decimals: int = self.token_contract.functions.decimals().call()
        self.PoW: Decimal = Decimal(10) ** Decimal(self.decimals)
        self.supply: Decimal = Decimal(self.token_contract.functions.totalSupply().call()) / self.PoW

    # @timer
    def find_trading_pair(self):
        """Trading pair: Find & Pick the trading pair with the most Liquidity available"""
        bnb_pair = self.factory_contract.functions.getPair(self.token.address, WBNB).call()
        busd_pair = self.factory_contract.functions.getPair(self.token.address, BUSD).call()
        usdt_pair = self.factory_contract.functions.getPair(self.token.address, USDT).call()

        if bnb_pair == default_pair_value and busd_pair == default_pair_value and usdt_pair == default_pair_value:
            self.to_print += f"Warning: {self.token.name} ({self.symbol}) No liquidity found.\n"
            self.error = True
            return

        pair_values_map = {}
        if bnb_pair != default_pair_value:
            (
                pair_values_map["bnb_pair"],
                is_bnb_reversed,
                bnb_pair_contract,
            ) = get_liquidity_reserve(self.w3, bnb_pair, WBNB, self.bnb_price)
        if busd_pair != default_pair_value:
            (
                pair_values_map["busd_pair"],
                is_busd_reversed,
                busd_pair_contract,
            ) = get_liquidity_reserve(self.w3, busd_pair, BUSD)
        if usdt_pair != default_pair_value:
            (
                pair_values_map["usdt_pair"],
                is_usdt_reversed,
                usdt_pair_contract,
            ) = get_liquidity_reserve(self.w3, usdt_pair, USDT)

        max_value_key = max(pair_values_map, key=pair_values_map.get)
        round_liquidity = self.w3.fromWei(pair_values_map[max_value_key], "ether").quantize(ETHER_NEG)

        if round_liquidity <= 0:
            self.to_print += f"Warning: {self.token.name} ({self.symbol}) No liquidity found.\n"
            self.error = True
            return

        bnb_liq = round_liquidity / self.bnb_price
        if max_value_key == "bnb_pair":
            self.is_reversed = is_bnb_reversed
            self.pair_contract = bnb_pair_contract
            self.counter_address = WBNB
            self.counter_symbol = "BNB"
        elif max_value_key == "busd_pair":
            self.is_reversed = is_busd_reversed
            self.pair_contract = busd_pair_contract
            self.counter_address = BUSD
            self.counter_symbol = "BUSD"
        else:
            self.is_reversed = is_usdt_reversed
            self.pair_contract = usdt_pair_contract
            self.counter_address = USDT
            self.counter_symbol = "USDT"

        self.buy_path_symbol = self.counter_symbol + " -> " + self.symbol
        self.sell_path_symbol = self.symbol + " -> " + self.counter_symbol
        self.to_print += (
            f"Trading pair: {self.symbol}/{self.counter_symbol} with liquidity = "
            f"{short_readable(round_liquidity)} USD ({short_readable(bnb_liq)} BNB)\n"
        )

    def find_transaction_path(self):
        """
        Transaction path: (Pay Token = BNB-BUSD-USDT)
            - Pay Token -> Buy Token
            - Pay Token -> Counter Pair -> Buy Token
        """

        if self.counter_symbol == "":
            return

        user_counter_pair_symbol = self.token.limit_trade.pay_currency

        if self.counter_symbol != user_counter_pair_symbol:

            self.buy_path_symbol = user_counter_pair_symbol + " -> " + self.buy_path_symbol
            self.sell_path_symbol = self.sell_path_symbol + " -> " + user_counter_pair_symbol

            if user_counter_pair_symbol == "BNB":
                tnx_path = [WBNB, self.counter_address, self.token.address]
            elif user_counter_pair_symbol == "BUSD":
                tnx_path = [BUSD, self.counter_address, self.token.address]
            else:
                tnx_path = [USDT, self.counter_address, self.token.address]

        else:
            tnx_path = [self.counter_address, self.token.address]

        self.buy_path: list[str] = tnx_path
        self.sell_path: list[str] = self.buy_path[::-1]

        self.to_print += f"Buy path : {self.buy_path_symbol}\n"
        self.to_print += f"Sell path: {self.sell_path_symbol}\n"

    def fetch_token_balance(self):
        self.token_balance_raw = get_token_balance_raw(self.token_contract, self.settings.wallet)
        self.token_balance = self.token_balance_raw / self.PoW
        self.to_print += f"Current {self.symbol} balance: {read_balance(self.token_balance)} {self.symbol}\n"
