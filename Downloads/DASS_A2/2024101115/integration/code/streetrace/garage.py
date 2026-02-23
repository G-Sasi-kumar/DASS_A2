"""Vehicle repair and maintenance module."""

from __future__ import annotations

from streetrace.crew_management import CrewManagementModule
from streetrace.inventory import InventoryModule


class GarageModule:
    """Handles vehicle repairs and maintenance."""

    def __init__(self, crew: CrewManagementModule, inventory: InventoryModule) -> None:
        """Initialize garage module."""
        self.crew = crew
        self.inventory = inventory

    def repair_car(self, car_id: int) -> bool:
        """Repair a damaged vehicle."""
        car = self.inventory.get_car(car_id)
        if not car:
            return False

        # Check if mechanic is available
        if not self.crew.has_role_available("mechanic"):
            return False

        # Repair the vehicle
        return self.inventory.repair_vehicle(car_id)

    def is_car_repairable(self, car_id: int) -> bool:
        """Check if a car can be repaired."""
        car = self.inventory.get_car(car_id)
        if not car:
            return False
        return car.damaged
