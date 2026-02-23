"""Finance module for income and expense tracking."""

from __future__ import annotations

from streetrace.inventory import InventoryModule


class FinanceModule:
    """Manages finance operations and synchronizes with inventory."""

    def __init__(self, inventory: InventoryModule) -> None:
        """Initialize finance module."""
        self.inventory = inventory
        self.ledger: list[tuple[str, int]] = []

    def record_income(self, description: str, amount: int) -> bool:
        """Record income and update inventory."""
        if amount <= 0:
            return False
        self.ledger.append((description, amount))
        return self.inventory.add_cash(amount)

    def record_expense(self, description: str, amount: int) -> bool:
        """Record expense if sufficient cash is available."""
        if amount <= 0:
            return False
        if amount > self.inventory.cash_balance:
            raise ValueError("Invalid cash spend - insufficient funds")
        self.ledger.append((description, -amount))
        return self.inventory.remove_cash(amount)

    def get_cash_balance(self) -> int:
        """Get current cash balance."""
        return self.inventory.cash_balance

    def get_ledger(self) -> list[tuple[str, int]]:
        """Get finance ledger."""
        return self.ledger
