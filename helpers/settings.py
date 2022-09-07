from dataclasses import dataclass


@dataclass
class Settings:
    """Wallet & transaction settings"""

    wallet: str = ""
    private_key: str = ""
    bcs_node: str = "https://bsc-dataseed1.defibit.io"
    gas_amount: int = 400000
    gas_price: float = 5.0
    revert_time: int = 5
    max_fail_attempts: int = 3

    def __repr__(self):
        return (
            f"{self.__class__.__name__}: "
            f"{self.wallet} {self.private_key} {self.bcs_node} {self.gas_amount} {self.gas_price} "
            f"{self.revert_time} {self.max_fail_attempts}"
        )
