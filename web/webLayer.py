import concurrent.futures
import os
from threading import Thread

import requests.exceptions

from helpers.settings import Settings
from helpers.tokens import *
from helpers.transaction import *
from helpers.utils import *

from .tokenData import TokenData
from .transactionsLayer import TransactionLayer


class WebLayer(Thread):
    """Run Web3 on new thread"""

    def __init__(self, tokens: list[Tokens], settings: Settings):
        super().__init__()
        self.dex_list: list[dict] = []
        self.settings = settings
        self.stop: bool = False
        self.fail_count = 0
        self.tokens = tokens
        self.init_abi()
        self.check_addresses_checksums_and_private_key()
        self.start()

    def init_abi(self):
        self.standard_abi = standard_abi
        self.LP_abi = LP_abi
        self.pancake_swap = pancake_swap
        self.bi_swap = bi_swap
        self.baby_swap = baby_swap
        self.ape_swap = ape_swap
        self.busta_swap = busta_swap

    def check_addresses_checksums_and_private_key(self):
        try:  # Wallet
            if self.settings.wallet == "":
                print("Warning: You need to insert your wallet in 'Settings'.")
                self.stop_thread()
                return
            self.settings.wallet = Web3.toChecksumAddress(self.settings.wallet)
        except ValueError:
            print(f"Error: please re-check your wallet address")
            self.stop_thread()
            return

        if self.settings.private_key == "":
            print("Warning: You need to insert your private key in 'Settings'.")
            self.stop_thread()
            return

        for token in self.tokens:
            try:  # Tokens
                if token.address == "":
                    print(f"Warning: You need to insert token address for token 'Name: {token.name}'.")
                    self.stop_thread()
                    return
                token.address = Web3.toChecksumAddress(token.address)
            except ValueError:
                print(f"Error: please re-check token address for token 'Name: {token.name}'")
                self.stop_thread()
                break

    def run(self):
        self.init_web3()
        self.account_balance()
        self.fetch_token_data()
        self.create_transactions_layer_list()
        self.main_loop()
        print("========================================")
        print("Info: Bot stopped trading.")

    @stop_trading
    @divider
    @timer
    def init_web3(self):
        """Initiate Web3 with HTTP node (For WSS you need Python 3.9)"""
        node = self.settings.bcs_node
        one_minute = int(time.time())
        while True:
            if node.startswith("w"):
                # self.web3 = Web3(Web3.WebsocketProvider(node))
                print("Sorry, you need python 3.9 to run WSS nodes.")
                print("Error: As of 3.10, the *loop* parameter was removed from Lock() since it is no longer necessary")
            else:
                self.web3 = Web3(Web3.HTTPProvider(node))

            if self.web3.isConnected():
                print("Info: Bsc node connected successfully.")
                break
            elif one_minute <= int(time.time()):
                one_minute = one_minute + 60
                print("Fail: Bsc connection failed. retry in 3 secs. . .")
            time.sleep(3)

    @stop_trading
    @divider
    def account_balance(self):
        """Wallet BNB, BUSD & USDT balances"""
        self.bnb_balance = get_bnb_balance_raw(self.web3, self.settings.wallet)
        print(f"Current BNB balance:  {raw_readable(self.bnb_balance)} BNB")

        self.BUSD_contract = self.web3.eth.contract(address=BUSD, abi=self.standard_abi)
        self.BUSD_balance = get_token_balance_raw(self.BUSD_contract, self.settings.wallet)
        print(f"Current BUSD balance: {raw_readable(self.BUSD_balance, 2)} BUSD")

        self.USDT_contract = self.web3.eth.contract(address=USDT, abi=self.standard_abi)
        self.USDT_balance = get_token_balance_raw(self.USDT_contract, self.settings.wallet)
        print(f"Current USDT balance: {raw_readable(self.USDT_balance, 2)} USDT")

        if self.bnb_balance < MIN_BNB:
            print("Warning: BNB balance too low for transaction fees.")
            self.stop_thread()

    @stop_trading
    @divider
    # @timer
    def fetch_token_data(self):
        """
        Fetch token data concurrently
        Remove tokens w/out liquidity or bought outside bot & save in list[TokenData]
        """
        self.init_tokens_dex()
        self.bnb_price = get_bnb_price(self.web3)
        try:
            self.tokens_data: list[TokenData] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = executor.map(self.work, self.tokens, self.dex_list)

                for i, result in enumerate(results):
                    print(result.to_print)
                    if not result.error and result.token.limit_trade.repetition > -1:
                        self.tokens_data.append(result)
                    elif result.token.limit_trade.repetition == -1:
                        print(f"Already traded with token '{self.tokens[i].name}' (No more Buy/Sell orders left).\n")
                    else:
                        print(f"Bot will not trade with Token '{self.tokens[i].name}'.\n")

                if len(self.tokens_data) == 0:
                    print("After filtering, no token available to trade with.")
                    self.stop_thread()

        except RuntimeError as e:
            print("Error (RuntimeError):", e)
        except requests.exceptions.HTTPError:
            print("Warning: Too many requests, retry in 5 secs . . .")
            time.sleep(5)

    def init_tokens_dex(self):
        """Create Dex list[dict] (contain dex data) to match list[Tokens] dex name"""
        for token in self.tokens:
            self.dex_list.append(
                self.pancake_swap
                if token.dex == "PancakeSwap v2"
                else self.bi_swap
                if token.dex == "BiSwap"
                else self.baby_swap
                if token.dex == "BabySwap"
                else self.ape_swap
                if token.dex == "ApeSwap"
                else self.busta_swap
                if token.dex == "BustaSwap"
                else self.pancake_swap
            )

    def work(self, token: Tokens, dex: dict) -> TokenData:
        return TokenData(self.web3, token, self.settings, dex, self.bnb_price)

    @stop_trading
    def create_transactions_layer_list(self):
        """Create list[TransactionLayer] from list[TokenData] left after filtering"""
        self.init_token_data_dex()
        self.transactions_layer: list[TransactionLayer] = []
        self.nonce = get_nonce(self.web3, self.settings.wallet)
        for i in range(len(self.tokens_data)):
            self.transactions_layer.append(
                TransactionLayer(
                    self.web3,
                    self.tokens_data[i],
                    self.settings,
                    self.dex_list[i],
                    self.nonce,
                    self.fail_count,
                )
            )

    def init_token_data_dex(self):
        """Create Dex list[dict] (contain dex data) to match list[TokenData] dex name"""
        self.dex_list.clear()
        for item in self.tokens_data:
            self.dex_list.append(
                self.pancake_swap
                if item.token.dex == "PancakeSwap v2"
                else self.bi_swap
                if item.token.dex == "BiSwap"
                else self.baby_swap
                if item.token.dex == "BabySwap"
                else self.ape_swap
                if token.dex == "ApeSwap"
                else self.busta_swap
                if token.dex == "BustaSwap"
                else self.pancake_swap
            )

    def main_loop(self):
        while not self.stop:
            self.start_trading()
            if self.settings.max_fail_attempts <= self.fail_count:
                print("========================================")
                print(
                    f'WARNING: Bot reached "Max Fail Transactions" ({self.settings.max_fail_attempts}) '
                    "set in Settings.\n"
                    "Info: Pressing 'START' will reset 'Max Fail Transactions Counter'."
                )
                self.stop_thread()

    @divider
    @timer
    def start_trading(self):
        """Initiate trading from list[TransactionLayer]"""
        try:
            completed_txn: list[Transaction] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                results = executor.map(self.init_transaction_layer, range(len(self.transactions_layer)))
                for index, result in enumerate(results):
                    print(result.to_print[:-1])  # Remove last \n
                    print("--------------------")

                    if result.update_files:
                        completed_txn.append(result.transaction)

            if len(completed_txn) != 0:
                self.save_transactions(completed_txn)
                self.save_tokens()

                if self.check_tokens_limit_orders_left():
                    self.account_balance()
                else:
                    print("========================================")
                    print("Info: All Tokens Limit Buy/Sell orders are filled.")
                    self.stop_thread()

        except requests.exceptions.HTTPError:
            print("Warning: Too many requests, retry in 5 secs . . .")
            time.sleep(5)
        except (RuntimeError, Exception) as e:
            print("Error: (Main)", e)
            self.stop_thread()

    def init_transaction_layer(self, index: int):
        return self.transactions_layer[index].start_limit_trading()

    @staticmethod
    def save_transactions(completed_txn: list[Transaction]):
        transaction_file = []
        try:
            with open("../transactions.json") as t_file:
                transaction_file = json.load(t_file)
        except (IOError, OSError) as sErr:
            if "No such file or directory" in str(sErr):
                with open("../transactions.json", "w") as t_file:
                    json.dump([], t_file)
            else:
                print(f"Error (Reading Transaction file): {sErr}")

        for item in completed_txn:
            txn = {
                "TIMESTAMP": item.time,
                "TXN_INITIATED_FROM": item.position,
                "TXN_STATUS": item.status,
                "TOKEN_NAME": item.name,
                "TOKEN_ADDRESS": item.address,
                "TOKEN_PRICE": item.price,
                "TXN_SLIPPAGE": item.slippage,
                "PAY/RECEIVED_AMOUNT": item.pay,
                "TOKEN_QUANTITY": item.quantity,
                "PROFIT": item.profit,
                "PROFIT_PERCENTAGE": item.profit_percentage,
                "TXN_PATH": item.txn_path,
                "GAS_PRICE": item.gas_price,
                "TXN_HASH": item.txn_hash,
            }
            transaction_file.append(txn)

        try:
            with open("../transactions.json", "w") as t_file:
                json.dump(transaction_file, t_file, indent=4)
        except (json.decoder.JSONDecodeError,) as sErr:
            print(f"Warning (Writing Transaction file): {str(sErr)}")
        except (IOError,) as sErr:
            print(f"Error (Reading Transaction file): {str(sErr)}")

        print("Info: Transaction(s) saved in file successfully.")

    def save_tokens(self):
        try:
            with open(os.path.join(os.getcwd(), "./data/tokens.json"), "w") as sFile:
                json.dump(self.tokens, sFile, indent=4, cls=DataClassJsonEncoder)
        except (OSError, IOError) as e:
            print("Error (Save tokens):", e)

    def check_tokens_limit_orders_left(self):
        """Check if all list[TransactionLayer] tokens orders repetition are done

        :return: bool: False if Done else True
        """
        for t_layer in self.transactions_layer:
            if t_layer.token_data.token.limit_trade.repetition == -1:
                continue
            return True
        return False

    def set_tokens(self, tokens: list[Tokens]):
        self.tokens = tokens

    def set_settings(self, settings: Settings):
        self.settings = settings

    def stop_thread(self):
        self.stop = True
