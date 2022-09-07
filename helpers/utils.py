import json
import time
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from hexbytes import HexBytes
from web3 import Web3, contract

from helpers.tokens import LimitTrade

""" CONSTANTS """
ETHER = Decimal(1000000000000000000)  # 10**18
ETHER_NEG = Decimal("0.000000000000000001")  # 10** -18
GWEI = Decimal(1000000000)
MIN_BNB = 400000 * (5 * GWEI)  # min txn fees
WBNB = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
BUSD = "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"
USDT = "0x55d398326f99059fF775485246999027B3197955"
busd_bnb_pair_adr = "0x58F876857a02D6762E0101bb5C46A8c1ED44Dc16"  # Default Busd/Bnb pair
default_pair_value = "0x0000000000000000000000000000000000000000"
approveAmount = 115792089237316195423570985008687907853269984665640564039457584007913129639935
transfer_address = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
APPROVE_ALLOWANCE = "APPROVE ALLOWANCE"
BUY = "BUY"
SELL = "SELL"


class Status(Enum):
    WAITING = 0
    SUCCESSFUL = "SUCCESSFUL"
    FAIL = "FAIL"


try:
    with open("./data/abi/standard.json") as file:
        standard_abi = json.load(file)

    with open("./data/abi/lp.json") as file:
        LP_abi = json.load(file)

    with open("./data/abi/pancake.json") as file:
        pancake_swap = json.load(file)

    with open("./data/abi/biswap.json") as file:
        bi_swap = json.load(file)

    with open("./data/abi/baby.json") as file:
        baby_swap = json.load(file)

    with open("./data/abi/ape.json") as file:
        ape_swap = json.load(file)

    with open("./data/abi/busta.json") as file:
        busta_swap = json.load(file)

except (
    OSError,
    IOError,
    KeyError,
    json.decoder.JSONDecodeError,
) as ex:
    print("Error importing files.", ex)


def read_balance(value: Decimal, dec: int = 18) -> str:
    return f"{value:,.{dec}f}".rstrip("0").rstrip(".")


def short_readable(value) -> str:  # 1.1234 -> 1.12
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def raw_readable(value: Decimal, dec: int = 8) -> str:  # (+10 ** 18) -> 1. dec
    value = value / ETHER
    return f"{value:,.{dec}f}".rstrip("0").rstrip(".")


def datetime_long() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_bnb_balance_raw(w3, wallet: str) -> Decimal:
    return Decimal(w3.eth.get_balance(wallet))


def get_token_balance_raw(token_contract: contract, wallet_adr: str) -> Decimal:
    return Decimal(token_contract.functions.balanceOf(wallet_adr).call())


def get_bnb_price(w3: Web3) -> Decimal:
    pair_contract = w3.eth.contract(address=busd_bnb_pair_adr, abi=LP_abi)
    (
        reserve0,
        reserve1,
        blockTimestampLast,
    ) = pair_contract.functions.getReserves().call()  # Bnb res, Busd res
    price = (Decimal(reserve1) / Decimal(reserve0)).quantize(ETHER_NEG)
    return price


def get_liquidity_reserve(
    w3: Web3, pair_address: str, counter_pair_address: str, bnb_price: Decimal = 0
) -> tuple[Decimal, bool, contract]:
    pair_contract = w3.eth.contract(address=pair_address, abi=LP_abi)
    (
        reserve0,
        reserve1,
        blockTimestampLast,
    ) = pair_contract.functions.getReserves().call()

    if (reserve0 or reserve1) == 0:  # Empty pool
        return Decimal(0), False, pair_contract
    else:
        # Is token0 = our token or pay token? (Bnb,busd,usdt)
        is_reversed = pair_contract.functions.token0().call() == counter_pair_address
        if is_reversed:
            peg_reserve = reserve0
        else:
            peg_reserve = reserve1

        if counter_pair_address == WBNB:
            peg_reserve = bnb_price * Decimal(peg_reserve)

        return Decimal(peg_reserve), is_reversed, pair_contract


def get_token_price(
    pair_contract: contract,
    is_reversed: bool,
    bnb_price: Decimal,
    counter_adr: str,
    t_pow: Decimal,
) -> tuple[Decimal, ...]:
    (
        reserve0,
        reserve1,
        blockTimestampLast,
    ) = pair_contract.functions.getReserves().call()

    reserve0 = Decimal(reserve0)
    reserve1 = Decimal(reserve1)

    if is_reversed:
        counter_reserve = reserve0
        token_reserve = reserve1
    else:
        counter_reserve = reserve1
        token_reserve = reserve0

    if counter_adr == WBNB:
        token_price_in_bnb = (counter_reserve / ETHER) / (token_reserve / t_pow)
        token_price = bnb_price * token_price_in_bnb
    else:
        token_price = (counter_reserve / ETHER) / (token_reserve / t_pow)
        token_price_in_bnb = token_price / bnb_price

    return token_price.quantize(ETHER_NEG), token_price_in_bnb.quantize(ETHER_NEG), token_reserve, counter_reserve


def get_allowance(token_contract: contract, wallet_adr: str, router_adr: str) -> int:
    return token_contract.functions.allowance(wallet_adr, router_adr).call()


""" Transaction Layer """


def get_nonce(w3: Web3, wallet_address: str) -> int:
    """Get wallet nonce (Current)"""
    # -1 because its giving us the next transaction nonce (we want the current and increment on every transaction)
    return w3.eth.get_transaction_count(wallet_address) - 1


def sign_and_send_transaction(w3: Web3, transaction: str, private_key: str) -> tuple[bool, HexBytes, str]:
    try:
        signed_txn = w3.eth.account.signTransaction(transaction, private_key)
    except (
        ValueError,
        TypeError,
    ):
        error_msg = "Error: (signing transaction): Please check that you got the correct Private Key for this wallet.\n"
        return False, HexBytes(""), error_msg

    try:
        tnx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        # w3.toHex(w3.keccak(signed_txn.rawTransaction))
    except (ValueError,) as vError:
        if "already known" in str(vError):
            error_msg = "Error: (Sending transaction): Nonce already used.\n"
        elif "nonce too low" in str(vError):
            error_msg = "Error: (Sending transaction): Nonce too low.\n"
        elif "replacement transaction underpriced" in str(vError):
            error_msg = "Error: (Sending transaction): Cannot use same nonce with lower gas.\n"
        else:
            error_msg = f"Error: (Sending transaction): {str(vError)}"
        return False, HexBytes(""), error_msg

    return True, tnx_hash, ""


def get_sold_amount(limit_obj: LimitTrade) -> Decimal:
    """Percentage of orders already sold"""
    percentage = Decimal(0)
    for i in range(len(limit_obj.order_done)):
        if limit_obj.order_done[i]:
            percentage += Decimal(limit_obj.sell_quantity[i])
    return percentage


def no_more_limit_sell_orders(limit_obj: LimitTrade) -> bool:
    """Check if all positive or negative orders are filled"""
    sold_positive = 0
    sold_negative = 0
    for i in range(len(limit_obj.sell_quantity)):
        if Decimal(limit_obj.sell_multiplier[i]) > 100 and (
            Decimal(limit_obj.sell_quantity[i]) == 0 or limit_obj.order_done[i]
        ):
            sold_positive += 1
        elif Decimal(limit_obj.sell_multiplier[i]) < 100 and (
            Decimal(limit_obj.sell_quantity[i]) == 0 or limit_obj.order_done[i]
        ):
            sold_negative += 1

    if sold_positive == 2 or sold_negative == 2:
        return True
    return False


def reset_token_file_after_limit_sell(limit_obj: LimitTrade) -> tuple[LimitTrade, str]:
    limit_obj.unit_buy_price = "0"
    limit_obj.qnt_bought = "0"

    for i in range(len(limit_obj.sell_quantity)):
        limit_obj.order_done[i] = False

    if limit_obj.repetition == 0 or limit_obj.repetition == limit_obj.rep_done:
        limit_obj.repetition = -1
        limit_obj.rep_done = 0
        msg = "Info: All {} positive or negative sell orders are filled, No more repetition left.\n"
    else:
        limit_obj.rep_done += 1
        msg = (
            "Info: Current {} "
            f"repetition count = {limit_obj.rep_done}, "
            f"repetition left = {limit_obj.repetition + 1 - limit_obj.rep_done}.\n"
        )

    return limit_obj, msg


""" DECORATORS """


def stop_trading(fun):
    def wrapper(self):
        if not self.stop:
            return fun(self)

    return wrapper


def timer(fun):
    def wrapper(self):
        starting_time = time.perf_counter()
        f = fun(self)
        print("End time = ", time.perf_counter() - starting_time)
        return f

    return wrapper


def divider(fun):
    def wrapper(self):
        print("========================================")
        f = fun(self)
        return f

    return wrapper
