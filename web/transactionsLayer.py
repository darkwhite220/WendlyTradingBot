import time

from web3 import exceptions

from helpers.settings import Settings
from helpers.transaction import Transaction
from helpers.utils import *

from .tokenData import TokenData


class TransactionLayer:
    """Transaction Layer:

    1-Get token price

    2-Buy

    3-Approve allowance

    4-Sell
    """

    def __init__(
        self,
        web3: Web3,
        token_data: TokenData,
        settings: Settings,
        dex: dict,
        nonce: int,
        fail_count: int,
    ):
        self.w3 = web3
        self.token_data = token_data
        self.settings = settings
        self.nonce = nonce
        self.fail_count = fail_count
        self.to_print: str = ""
        self.limit_trade = self.token_data.token.limit_trade
        self.unit_buy_price = Decimal(self.limit_trade.unit_buy_price)
        self.qnt_bought = Decimal(self.limit_trade.qnt_bought)
        self.pay_currency = self.limit_trade.pay_currency
        self.swap_fee = Decimal(dex["FEE"])
        self.t_symbol = token_data.symbol
        self.PoW = token_data.PoW
        self.update_files: bool = False
        self.transaction = Transaction()
        self.txn_hex: HexBytes = HexBytes("")

    def start_limit_trading(self) -> "TransactionLayer":
        self.to_print = ""  # reset

        # Check if a transaction is waiting results
        if self.pending_transaction_result():
            return self

        if self.check_allowance():
            return self

        # Check Repetition
        if self.limit_trade.repetition < 0:
            self.to_print += (
                f"Info: Already traded with token '{self.token_data.token.name}', Reset it by "
                f"selecting 'Repetition' to min value of 0.\n"
            )
            return self

        # Get & Display token price
        self.get_token_price()

        # Sell
        if self.qnt_bought > 0 and self.token_data.token_balance_raw > 0:  # Sell
            for i in range(len(self.limit_trade.order_done)):
                if self.limit_trade.order_done[i]:
                    continue

                # Sell when current_multi >= sell_multi on profit, Or when current_multi <= sell_multi on loss
                if (self.current_multi >= Decimal(self.limit_trade.sell_multiplier[i]) > 100) or (
                    self.current_multi <= Decimal(self.limit_trade.sell_multiplier[i]) < 100
                ):

                    # Sell quantity (max amount = what we bought from THIS limit buy)
                    pct_already_sold = get_sold_amount(self.limit_trade)
                    max_pct_to_sell = min(
                        Decimal(self.limit_trade.sell_quantity[i]),
                        100 - pct_already_sold,
                    )
                    self.sell_quantity_raw = min(
                        self.qnt_bought * max_pct_to_sell / 100,
                        self.token_data.token_balance_raw,
                    )
                    self.sell_quantity = self.sell_quantity_raw / self.PoW

                    self.tokens_left_from_ord = (self.qnt_bought - self.sell_quantity_raw) / self.PoW

                    self.transaction.position = f"Limit Sell -> Order {i + 1}"
                    self.limit_sell_pos: int = i
                    status, txn_hex, error_msg = self.sell(int(self.sell_quantity_raw))

                    if status:
                        self.txn_hex = txn_hex
                        self.transaction.txn_hash = self.w3.toHex(txn_hex)
                        self.to_print += f"{self.t_symbol} Sell Transaction Hash: {self.transaction.txn_hash}\n"
                    else:  # reset
                        self.nonce -= 1
                        self.to_print += error_msg
                        self.transaction = Transaction()

        # Buy
        elif self.token_price_usd < Decimal(self.limit_trade.buy_at) and self.qnt_bought == 0:  # Buy

            status, txn_hex, error_msg = self.buy()
            self.transaction.position = "Limit Buy"
            if status:
                self.txn_hex = txn_hex
                self.transaction.txn_hash = self.w3.toHex(txn_hex)
                self.to_print += f"{self.t_symbol} Buy Transaction Hash: {self.transaction.txn_hash}\n"
            else:  # reset
                self.nonce -= 1
                self.to_print += error_msg
                self.transaction = Transaction()

        return self

    def pending_transaction_result(self) -> bool:
        """Get pending transaction status, if we get a response update Transaction & ask WebLayer to save files (
        transaction.json, tokens.json)"""
        if self.txn_hex != HexBytes(""):
            status, received_amount_raw = self.wait_transaction_status()

            if status == Status.WAITING:
                self.update_files = False
                return True
            elif status == Status.SUCCESSFUL:
                self.transaction.status = Status.SUCCESSFUL.value

                if self.transaction.txn_type == BUY:
                    self.calculations_after_buy(received_amount_raw)
                    self.token_data.token_balance_raw += received_amount_raw  # Update balance

                elif self.transaction.txn_type == SELL:
                    self.calculations_after_sell(received_amount_raw)
                    self.token_data.token_balance_raw -= self.sell_quantity_raw  # Update balance
                    self.token_data.token_balance -= self.sell_quantity

                    # Reset token limit orders if no more tokens left from buy order, else update it
                    if self.tokens_left_from_ord == 0 or no_more_limit_sell_orders(self.limit_trade):
                        self.limit_trade, msg = reset_token_file_after_limit_sell(self.limit_trade)  # repetition update
                        self.to_print += msg.format(self.t_symbol)
                    else:
                        self.limit_trade.order_done[self.limit_sell_pos] = True

                else:
                    self.token_data.allowance = approveAmount
                    self.wait_approval_update()

            else:
                self.transaction.status = Status.FAIL.value
                self.fail_count += 1

            self.transaction.address = self.token_data.token.address
            self.transaction.name = f"{self.token_data.token.name} ({self.t_symbol})"
            self.update_files = True

            # Reset
            self.unit_buy_price = Decimal(self.limit_trade.unit_buy_price)
            self.txn_hex = HexBytes("")
            return True
        # Reset
        self.transaction = Transaction()
        self.update_files = False
        return False

    def check_allowance(self) -> bool:
        """Approve token allowance after buy"""
        if self.qnt_bought > 0 and self.token_data.allowance <= self.token_data.token_balance_raw:
            self.to_print += "Token need approval to sell, Sending approve allowance request . . .\n"
            self.transaction.txn_type = APPROVE_ALLOWANCE
            self.transaction.position = APPROVE_ALLOWANCE.capitalize()
            try:
                self.deadline = int(time.time()) + self.settings.revert_time * 60
                self.nonce += 1
                transaction = self.token_data.token_contract.functions.approve(
                    self.token_data.router_address, approveAmount
                ).buildTransaction(
                    {
                        "from": self.settings.wallet,
                        "gasPrice": int(Decimal(self.settings.gas_price) * GWEI),
                        "nonce": self.nonce,
                    }
                )

                status, txn_hex, error_msg = sign_and_send_transaction(self.w3, transaction, self.settings.private_key)

                if status:
                    self.txn_hex = txn_hex
                    self.transaction.txn_hash = self.w3.toHex(txn_hex)
                    self.to_print += f"{self.t_symbol} Approve Transaction Hash: {self.transaction.txn_hash}\n"
                else:
                    self.nonce -= 1
                    self.to_print += error_msg
                    self.transaction = Transaction()

            except (ValueError,) as approveError:
                if "gas required exceeds allowance" in str(approveError):
                    self.to_print += "Error: (Low BNB): Low bnb balance to pay gas fees.\n"
                else:
                    self.to_print += f"Error (Approve token): {str(approveError)}\n"
            return True
        return False

    def get_token_price(self):
        (self.token_price_usd, self.token_price_bnb, self.token_reserve, self.counter_reserve,) = get_token_price(
            self.token_data.pair_contract,
            self.token_data.is_reversed,
            self.token_data.bnb_price,
            self.token_data.counter_address,
            self.PoW,
        )

        multiplier = ""
        if self.unit_buy_price != 0:
            if self.pay_currency == "BNB":
                self.current_multi = self.token_price_bnb / self.unit_buy_price * 100
                multiplier = f"({round(self.current_multi, 2)}%)"
            else:
                self.current_multi = self.token_price_usd / self.unit_buy_price * 100
                multiplier = f"({round(self.current_multi, 2)}%)"

        self.to_print += (
            f"{self.t_symbol} price: ".ljust(13)
            + f"{read_balance(self.token_price_usd)} USD | ".rjust(26)
            + f"{read_balance(self.token_price_bnb)} BNB".rjust(23)
            + f" {multiplier}\n"
        )

    def buy(self) -> tuple[bool, HexBytes, str]:
        """
        Create BUY Transaction then Sign & Send it to BlockChain.

        return:
            bool: Error or Successful

            Hexbytes: Transaction hexbytes

            string: error message
        """

        self.pay_amount = Decimal(self.limit_trade.pay_amount)

        self.transaction.txn_type = BUY
        self.transaction.pay = str(self.pay_amount) + " " + self.pay_currency
        self.transaction.txn_path = self.token_data.buy_path_symbol

        pay_amount = int(self.pay_amount * ETHER)
        slippage = Decimal(self.token_data.token.slippage)

        if slippage >= 100:
            amount_out = 0
        else:
            # Deduct DEX swap fee from pay amount
            pay_amount_after_fee = self.pay_amount - (self.pay_amount * self.swap_fee / 100).quantize(ETHER_NEG)
            if self.pay_currency == "BNB":
                amount_out = (pay_amount_after_fee / self.token_price_bnb) * ((100 - slippage) / 100)
            else:
                amount_out = (pay_amount_after_fee / self.token_price_usd) * ((100 - slippage) / 100)
            amount_out = int(amount_out * self.PoW)

        self.deadline = int(time.time()) + self.settings.revert_time * 60
        self.gas_price = int(Decimal(self.settings.gas_price) * GWEI)

        try:
            self.to_print += (
                f"Initiating {self.t_symbol} buy transaction: {self.transaction.pay} "
                f"(Path: {self.token_data.buy_path_symbol}).\n"
            )
            self.nonce += 1
            if self.pay_currency == "BNB":
                transaction = (
                    self.token_data.router_contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
                        amount_out,
                        self.token_data.buy_path,
                        self.settings.wallet,
                        self.deadline,
                    ).buildTransaction(
                        {
                            "from": self.settings.wallet,
                            "value": pay_amount,
                            "gasPrice": self.gas_price,
                            "gas": self.settings.gas_amount,
                            "nonce": self.nonce,
                        }
                    )
                )
            else:
                transaction = (
                    self.token_data.router_contract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                        pay_amount,
                        amount_out,
                        self.token_data.buy_path,
                        self.settings.wallet,
                        self.deadline,
                    ).buildTransaction(
                        {
                            "gasPrice": self.gas_price,
                            "gas": self.settings.gas_amount,
                            "from": self.settings.wallet,
                            "nonce": self.nonce,
                        }
                    )
                )

            return sign_and_send_transaction(self.w3, transaction, self.settings.private_key)

        except exceptions.ContractLogicError as cl_error:
            error_msg = f"Error (Buy transaction CLE): {str(cl_error)}\n"

        except (ValueError,) as ve_error:
            error_msg = f"Error (Buy transaction VE): {str(ve_error)}\n"
        return False, HexBytes(""), error_msg

    def sell(self, sell_quantity_raw: int) -> tuple[bool, HexBytes, str]:
        """
        Create a SELL Transaction then Sign & Send it to BlockChain.

        return:
            bool: Error or Successful

            Hexbytes: Transaction hexbytes

            string: error message
        """

        self.transaction.txn_type = SELL
        self.transaction.pay = read_balance(self.sell_quantity) + " " + self.t_symbol
        self.transaction.txn_path = self.token_data.sell_path_symbol

        slippage = Decimal(self.token_data.token.slippage)

        if slippage == 100:
            amount_out = 0
        else:
            # Deduct DEX swap fee from pay amount
            sell_quantity_after_fee = self.sell_quantity - (self.sell_quantity * self.swap_fee / 100).quantize(
                1 / self.PoW
            )
            if self.pay_currency == "BNB":
                amount_out = sell_quantity_after_fee * self.token_price_bnb * ((100 - slippage) / 100)
            else:
                amount_out = sell_quantity_after_fee * self.token_price_usd * ((100 - slippage) / 100)
            amount_out = int(amount_out * ETHER)

        self.deadline = int(time.time()) + self.settings.revert_time * 60
        self.gas_price = int(Decimal(self.settings.gas_price) * GWEI)

        try:
            self.to_print += (
                f"Initiating {self.t_symbol} sell transaction: {self.transaction.pay}, "
                f"{self.transaction.position} (Path: {self.token_data.sell_path_symbol}).\n"
            )
            self.nonce += 1
            if self.pay_currency == "BNB":
                transaction = (
                    self.token_data.router_contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                        sell_quantity_raw,
                        amount_out,
                        self.token_data.sell_path,
                        self.settings.wallet,
                        self.deadline,
                    ).buildTransaction(
                        {
                            "from": self.settings.wallet,
                            "gasPrice": self.gas_price,
                            "gas": self.settings.gas_amount,
                            "nonce": self.nonce,
                        }
                    )
                )
            else:
                transaction = (
                    self.token_data.router_contract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
                        sell_quantity_raw,
                        amount_out,
                        self.token_data.sell_path,
                        self.settings.wallet,
                        self.deadline,
                    ).buildTransaction(
                        {
                            "gasPrice": self.gas_price,
                            "gas": self.settings.gas_amount,
                            "from": self.settings.wallet,
                            "nonce": self.nonce,
                        }
                    )
                )
            return sign_and_send_transaction(self.w3, transaction, self.settings.private_key)

        except exceptions.ContractLogicError as cl_error:
            error_msg = f"Error (Sell transaction CLE): {str(cl_error)}\n"

        except (ValueError,) as ve_error:
            error_msg = f"Error (Sell transaction VE): {str(ve_error)}\n"
        return False, HexBytes(""), error_msg

    def wait_transaction_status(self) -> tuple[Status, Decimal]:
        try:
            response: TxReceipt = self.w3.eth.get_transaction_receipt(self.txn_hex)  # -> TxReceipt
            response: dict = json.loads(Web3.toJSON(response))  # TxReceipt-> String -> dict
            self.transaction.time = datetime_long()

            status = response["status"]
            gas_used = Decimal(response["gasUsed"])
            amount = 0

            if status == 1:
                status = "SUCCESSFUL"
                if self.transaction.txn_type != APPROVE_ALLOWANCE:
                    # Token amount we bought Or Pay amount (BNB/BUSD/USDT) we got after sell
                    amount = [item["data"] for item in response["logs"] if item["topics"][0] == transfer_address][-1]
                    amount = int(amount, 16)  # Convert: hex -> str -> int
            else:
                status = "FAIL"

            self.txn_gas_price = gas_used * Decimal(self.gas_price) / ETHER
            self.transaction.gas_price = read_balance(self.txn_gas_price) + " BNB"
            self.to_print += f"Transaction Status: {status}\nTransaction Hash: {self.transaction.txn_hash}\n"

            return Status.SUCCESSFUL if status == "SUCCESSFUL" else Status.FAIL, Decimal(amount)  # int -> Decimal

        except (exceptions.TransactionNotFound,) as e:
            if "not found" in str(e):
                self.to_print += (
                    f"{self.t_symbol} {self.transaction.txn_type} " f"transaction waiting confirmation . . .\n"
                )
                return Status.WAITING, Decimal(0)
            elif self.deadline + 10 < int(time.time()):
                self.to_print += (
                    "Warning: Confirmation taking too long, Automatic checking stopped, "
                    'transaction "revert time" + 10 seconds passed. Resuming and taking transaction '
                    'status as "FAIL".\n'
                )
            else:
                self.to_print += (
                    f"Error (getTransactionReceipt): {str(e)}\n" + f"{self.transaction.txn_type} transaction failed.\n"
                )

            return Status.FAIL, Decimal(0)

    def wait_approval_update(self):
        while True:
            allowance = get_allowance(
                self.token_data.token_contract,
                self.settings.wallet,
                self.token_data.router_address,
            )

            if allowance == approveAmount:
                break
        self.to_print += f"Info: (Token {self.token_data.token.name}) allowance updated.\n"

    def calculations_after_buy(self, bought_amount_raw: Decimal):
        buy_quantity_raw = bought_amount_raw
        buy_quantity = buy_quantity_raw / self.PoW
        # w/ Tax
        unit_buy_price = (self.pay_amount / buy_quantity).quantize(ETHER_NEG)
        # w/out dex swap fee
        unit_buy_price_no_fee = (
            (self.pay_amount - (self.pay_amount * self.swap_fee / 100).quantize(ETHER_NEG)) / buy_quantity
        ).quantize(ETHER_NEG)
        self.transaction.quantity = f"{read_balance(buy_quantity)} {self.t_symbol}"
        self.transaction.price = f"{read_balance(unit_buy_price)} {self.pay_currency}"
        # Update token file values
        self.limit_trade.qnt_bought = str(buy_quantity_raw)
        self.limit_trade.unit_buy_price = "{:.18f}".format(unit_buy_price)
        # update val
        self.qnt_bought = buy_quantity_raw

        # Slippage
        if self.pay_currency == "BNB":
            total_slippage = 100 - self.token_price_bnb * 100 / unit_buy_price_no_fee
        else:
            total_slippage = 100 - self.token_price_usd * 100 / unit_buy_price_no_fee

        str_ttl_slippage = self.print_slippage(total_slippage)
        self.transaction.slippage = f"{str_ttl_slippage}% + ({self.token_data.token.dex} fee {self.swap_fee}%)"

        calculated_slippage = total_slippage - Decimal(self.token_data.token.buy_tax)
        addition = "+"
        if calculated_slippage < 0:
            calculated_slippage = abs(calculated_slippage)
            addition = "-"

        self.to_print += f"Bought: {self.transaction.quantity} with {self.transaction.pay}\n"
        self.to_print += (
            f"Total Slippage (Buy Tax, Slippage): {self.token_data.token.buy_tax} {addition} "
            f"{round(calculated_slippage, 2)} = {str_ttl_slippage}%\n"
        )
        self.to_print += (
            f"Current {self.t_symbol} balance: "
            f"{read_balance(self.token_data.token_balance + buy_quantity)} {self.t_symbol}\n"
        )

    def calculations_after_sell(self, received_amount_raw: Decimal):
        received_amount = received_amount_raw / ETHER

        sell_quantity_after_fee = self.sell_quantity - (self.sell_quantity * self.swap_fee / 100).quantize(1 / self.PoW)

        unit_sell_price_no_fee = (received_amount / sell_quantity_after_fee).quantize(ETHER_NEG)

        # How much we bought this quantity
        how_much_we_paid = (Decimal(self.limit_trade.unit_buy_price) * self.sell_quantity).quantize(ETHER_NEG)

        profit = received_amount - how_much_we_paid
        diff_pct = received_amount / how_much_we_paid * 100

        self.transaction.price = f"{read_balance(unit_sell_price_no_fee)} {self.pay_currency}"
        self.transaction.pay = f"{read_balance(received_amount)} {self.pay_currency}"
        self.transaction.quantity = f"{read_balance(self.sell_quantity)} {self.t_symbol}"
        self.transaction.profit = f"{read_balance(profit)} {self.pay_currency}"
        self.transaction.profit_percentage = f"{round(diff_pct, 2)}%"

        # Slippage
        if self.pay_currency == "BNB":
            total_slippage = 100 - unit_sell_price_no_fee * 100 / self.token_price_bnb
        else:
            total_slippage = 100 - unit_sell_price_no_fee * 100 / self.token_price_usd

        str_ttl_slippage = self.print_slippage(total_slippage)
        self.transaction.slippage = f"{str_ttl_slippage}% + ({self.token_data.token.dex} fee {self.swap_fee}%)"

        calculated_slippage = total_slippage - Decimal(self.token_data.token.sell_tax)
        plus_minus = "+"
        if calculated_slippage < 0:
            calculated_slippage = abs(calculated_slippage)
            plus_minus = "-"

        self.to_print += (
            f"Sold: {read_balance(self.sell_quantity)} {self.t_symbol} ({self.transaction.position})"
            f" for {read_balance(received_amount)} {self.pay_currency}\n"
        )
        self.to_print += (
            f"Total Slippage (Sell Tax, Slippage): {self.token_data.token.sell_tax} {plus_minus} "
            f"{round(calculated_slippage, 2)} = {str_ttl_slippage}%\n"
        )

        self.to_print += f"Profit: {self.transaction.profit} ({self.transaction.profit_percentage})\n"
        self.to_print += (
            f"Current {self.t_symbol} balance left from buy order:"
            f" {read_balance(self.tokens_left_from_ord)} {self.t_symbol}\n"
        )
        self.to_print += (
            f"Total {self.t_symbol} balance: " f"{read_balance(self.token_data.token_balance)} {self.t_symbol}\n"
        )

    @staticmethod
    def print_slippage(slippage: Decimal) -> str:
        if slippage < Decimal("-0.01"):
            return "< -0.01"
        elif 0 < slippage < Decimal("0.01"):
            return "< 0.01"
        else:
            return str(round(slippage, 2))
