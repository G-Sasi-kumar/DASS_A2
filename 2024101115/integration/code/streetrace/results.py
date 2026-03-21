"""Race results processing and updates."""

from __future__ import annotations

from streetrace.inventory import InventoryModule


class ResultsModule:
    """Processes race results and updates inventory."""

    def __init__(self, inventory: InventoryModule) -> None:
        """Initialize results module."""
        self.inventory = inventory
        self.rankings = {}

    def record_result(
        self,
        race: object,
        member_ids: list[int],
        damaged_car_ids: list[int] | None = None,
    ) -> bool:
        """Record race result and award prize money and rankings."""
        if not member_ids:
            return False

        # Award prize money to the winner
        if len(member_ids) > 0:
            self.inventory.add_cash(race.prize_money if hasattr(race, "prize_money") else 0)

        # Assign ranking points: 1st = 10 pts, 2nd = 4 pts, 3rd = 3 pts, 4th = 2 pts
        ranking_points = [10, 4, 3, 2]
        for idx, member_id in enumerate(member_ids):
            points = ranking_points[idx] if idx < len(ranking_points) else 0
            self.rankings[member_id] = points

        # Mark damaged cars
        if damaged_car_ids:
            for car_id in damaged_car_ids:
                self.inventory.damage_vehicle(car_id)

        return True

    def get_rankings(self) -> dict[int, int]:
        """Get current rankings."""
        return self.rankings
