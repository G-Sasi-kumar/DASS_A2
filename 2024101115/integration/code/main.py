"""Small runnable demo for the StreetRace Manager submission."""

from streetrace.crew_management import CrewManagementModule
from streetrace.finance import FinanceModule
from streetrace.garage import GarageModule
from streetrace.inventory import InventoryModule
from streetrace.mission_planning import MissionPlanningModule
from streetrace.race_management import RaceManagementModule
from streetrace.registration import RegistrationModule
from streetrace.results import ResultsModule


def main() -> None:
    """Run a small happy-path integration demo."""
    registration = RegistrationModule()
    crew = CrewManagementModule(registration)
    inventory = InventoryModule()
    races = RaceManagementModule(registration, crew, inventory)
    results = ResultsModule(inventory)
    missions = MissionPlanningModule(crew)
    garage = GarageModule(crew, inventory)
    finance = FinanceModule(inventory)

    driver = registration.register_member("Aarav", "driver")
    mechanic = registration.register_member("Meera", "mechanic")
    crew.set_skill_level(driver.member_id, 5)
    crew.assign_role(mechanic.member_id, "mechanic")

    car = inventory.add_car("Skyline")
    race = races.create_race("Night Sprint", 5000)
    races.enter_race(race.race_id, driver.member_id, car.car_id)
    results.record_result(race, [driver.member_id], damaged_car_ids=[car.car_id])
    garage.repair_car(car.car_id)
    mission = missions.create_mission("Recovery Run", ["driver", "mechanic"])
    missions.start_mission(mission.mission_id)
    finance.record_income("Prize payout", 500)

    print("StreetRace Manager demo completed successfully.")
    print(f"Cash balance: {inventory.cash_balance}")
    print(f"Mission status: {mission.status}")
    print(f"Car damaged: {inventory.get_car(car.car_id).damaged}")


if __name__ == "__main__":
    main()
