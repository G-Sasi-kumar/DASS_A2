"""Inventory and cash management."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Car:
    """Represents a vehicle in inventory."""

    car_id: int
    name: str
    assigned_driver_id: int | None = None
    damaged: bool = False


class InventoryModule:
    """Manages inventory and financial resources."""

    def __init__(self) -> None:
        """Initialize inventory module."""
        self.cash_balance = 0
        self.cars = {}
        self.next_car_id = 1

    def add_car(self, car_name: str) -> Car:
        """Add a vehicle to inventory."""
        car_id = self.next_car_id
        self.next_car_id += 1
        car = Car(car_id=car_id, name=car_name)
        self.cars[car_id] = car
        return car

    def get_car(self, car_id: int) -> Car | None:
        """Get a car by ID."""
        return self.cars.get(car_id)

    def add_cash(self, amount: int) -> bool:
        """Add cash to inventory."""
        if amount <= 0:
            return False
        self.cash_balance += amount
        return True

    def remove_cash(self, amount: int) -> bool:
        """Remove cash from inventory."""
        if amount <= 0 or amount > self.cash_balance:
            return False
        self.cash_balance -= amount
        return True

    def damage_vehicle(self, car_id: int) -> bool:
        """Mark a vehicle as damaged."""
        car = self.cars.get(car_id)
        if not car:
            return False
        car.damaged = True
        return True

    def repair_vehicle(self, car_id: int) -> bool:
        """Repair a damaged vehicle."""
        car = self.cars.get(car_id)
        if not car:
            return False
        car.damaged = False
        return True

    def is_vehicle_damaged(self, car_id: int) -> bool:
        """Check if a vehicle is damaged."""
        car = self.cars.get(car_id)
        if not car:
            return False
        return car.damaged
