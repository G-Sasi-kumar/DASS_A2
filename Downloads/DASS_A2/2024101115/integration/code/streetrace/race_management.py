"""Race management and entry handling."""

from __future__ import annotations

from dataclasses import dataclass, field

from streetrace.crew_management import CrewManagementModule
from streetrace.inventory import InventoryModule
from streetrace.registration import RegistrationModule


@dataclass
class Race:
    """Represents a race event."""

    race_id: int
    name: str
    prize_money: int
    entrants: list[tuple[int, int]] = field(default_factory=list)


class RaceManagementModule:
    """Manages race entries and race-related operations."""

    def __init__(
        self,
        registration: RegistrationModule,
        crew: CrewManagementModule,
        inventory: InventoryModule,
    ) -> None:
        """Initialize race management."""
        self.registration = registration
        self.crew = crew
        self.inventory = inventory
        self.races = {}
        self.next_race_id = 1

    def create_race(self, name: str, prize_money: int) -> Race:
        """Create a new race."""
        race_id = self.next_race_id
        self.next_race_id += 1
        race = Race(race_id=race_id, name=name, prize_money=prize_money)
        self.races[race_id] = race
        return race

    def enter_race(self, race_id: int, member_id: int, car_id: int) -> bool:
        """Register a driver and vehicle for a race."""
        race = self.races.get(race_id)
        if not race:
            return False

        # Check if driver exists
        member = self.registration.get_member(member_id)
        if not member:
            raise ValueError("Unknown crew member id")

        # Check if driver has driver role
        if member.role != "driver":
            raise ValueError("Only drivers can enter races")

        # Check if driver is available
        if not self.crew.is_available(member_id):
            raise ValueError("Driver is unavailable for racing")

        # Check if car exists
        car = self.inventory.get_car(car_id)
        if not car:
            return False

        # Check if car is not damaged
        if car.damaged:
            raise ValueError("Car is not race-ready (damaged)")

        # Add to race entrants
        race.entrants.append((member_id, car_id))
        car.assigned_driver_id = member_id
        return True

    def get_race(self, race_id: int) -> Race | None:
        """Get race by ID."""
        return self.races.get(race_id)
