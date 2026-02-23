"""Integration tests for StreetRace Manager."""

from __future__ import annotations

import pytest

from streetrace.crew_management import CrewManagementModule
from streetrace.finance import FinanceModule
from streetrace.garage import GarageModule
from streetrace.inventory import InventoryModule
from streetrace.mission_planning import MissionPlanningModule
from streetrace.race_management import RaceManagementModule
from streetrace.registration import RegistrationModule
from streetrace.results import ResultsModule


def build_modules() -> dict[str, object]:
    """Create a fresh integration graph for each case."""
    registration = RegistrationModule()
    crew = CrewManagementModule(registration)
    inventory = InventoryModule()
    races = RaceManagementModule(registration, crew, inventory)
    results = ResultsModule(inventory)
    missions = MissionPlanningModule(crew)
    garage = GarageModule(crew, inventory)
    finance = FinanceModule(inventory)
    return {
        "registration": registration,
        "crew": crew,
        "inventory": inventory,
        "races": races,
        "results": results,
        "missions": missions,
        "garage": garage,
        "finance": finance,
    }


ENTRY_CASES = [
    (f"Driver {index}", f"Car {index}", 1000 + (index * 150))
    for index in range(1, 21)
]
UNKNOWN_MEMBER_IDS = list(range(900, 920))
NON_DRIVER_ROLES = ["mechanic", "strategist", "navigator", "scout", "medic"] * 4
UNAVAILABLE_DRIVER_CASES = [
    (f"Unavailable Driver {index}", f"Idle Car {index}", 2000 + (index * 75))
    for index in range(1, 21)
]
DAMAGED_CAR_CASES = [
    (f"Damaged Driver {index}", f"Damaged Car {index}", 1500 + (index * 50))
    for index in range(1, 21)
]
RESULT_CASES = [
    (1200 + (index * 200), [10, 4, 3, 2][: ((index - 1) % 4) + 1])
    for index in range(1, 21)
]
MISSION_UNAVAILABLE_CASES = [
    ["driver"],
    ["mechanic"],
    ["strategist"],
    ["driver", "mechanic"],
    ["driver", "strategist"],
    ["mechanic", "strategist"],
    ["driver", "mechanic", "strategist"],
    ["navigator"],
    ["driver", "navigator"],
    ["mechanic", "navigator"],
] * 2
MISSION_AVAILABLE_CASES = [
    ["driver"],
    ["mechanic"],
    ["strategist"],
    ["driver", "mechanic"],
    ["driver", "strategist"],
    ["mechanic", "strategist"],
    ["driver", "mechanic", "strategist"],
    ["navigator"],
    ["driver", "navigator"],
    ["mechanic", "navigator"],
] * 2
FINANCE_SUCCESS_CASES = [
    (3000 + (index * 250), 500 + (index * 40))
    for index in range(1, 21)
]
FINANCE_INVALID_EXPENSE_CASES = [
    (1000 + (index * 50), 2000 + (index * 75))
    for index in range(1, 21)
]


@pytest.mark.parametrize(("driver_name", "car_name", "prize_money"), ENTRY_CASES)
def test_registered_driver_can_enter_race(
    driver_name: str,
    car_name: str,
    prize_money: int,
) -> None:
    modules = build_modules()
    registration = modules["registration"]
    crew = modules["crew"]
    inventory = modules["inventory"]
    races = modules["races"]

    driver = registration.register_member(driver_name, "driver")
    crew.set_skill_level(driver.member_id, 5)
    car = inventory.add_car(car_name)
    race = races.create_race(f"{driver_name} Grand Prix", prize_money)

    races.enter_race(race.race_id, driver.member_id, car.car_id)

    assert race.entrants == [(driver.member_id, car.car_id)]
    assert car.assigned_driver_id == driver.member_id


@pytest.mark.parametrize("unknown_member_id", UNKNOWN_MEMBER_IDS)
def test_unregistered_driver_cannot_enter_race(unknown_member_id: int) -> None:
    modules = build_modules()
    inventory = modules["inventory"]
    races = modules["races"]

    car = inventory.add_car("Fallback Car")
    race = races.create_race("Midnight Run", 4000)

    with pytest.raises(ValueError, match="Unknown crew member id"):
        races.enter_race(race.race_id, unknown_member_id, car.car_id)


@pytest.mark.parametrize("role", NON_DRIVER_ROLES)
def test_only_drivers_can_enter_race(role: str) -> None:
    modules = build_modules()
    registration = modules["registration"]
    inventory = modules["inventory"]
    races = modules["races"]

    member = registration.register_member(f"{role.title()} Crew", role)
    car = inventory.add_car("RX-7")
    race = races.create_race("Dock Dash", 3000)

    with pytest.raises(ValueError, match="Only drivers"):
        races.enter_race(race.race_id, member.member_id, car.car_id)


@pytest.mark.parametrize(("driver_name", "car_name", "prize_money"), UNAVAILABLE_DRIVER_CASES)
def test_unavailable_driver_cannot_enter_race(
    driver_name: str,
    car_name: str,
    prize_money: int,
) -> None:
    modules = build_modules()
    registration = modules["registration"]
    crew = modules["crew"]
    inventory = modules["inventory"]
    races = modules["races"]

    driver = registration.register_member(driver_name, "driver")
    crew.set_availability(driver.member_id, False)
    car = inventory.add_car(car_name)
    race = races.create_race("Unavailable Cup", prize_money)

    with pytest.raises(ValueError, match="unavailable"):
        races.enter_race(race.race_id, driver.member_id, car.car_id)


@pytest.mark.parametrize(("driver_name", "car_name", "prize_money"), DAMAGED_CAR_CASES)
def test_damaged_car_requires_repair_before_next_race(
    driver_name: str,
    car_name: str,
    prize_money: int,
) -> None:
    modules = build_modules()
    registration = modules["registration"]
    crew = modules["crew"]
    inventory = modules["inventory"]
    races = modules["races"]
    results = modules["results"]
    garage = modules["garage"]

    driver = registration.register_member(driver_name, "driver")
    mechanic = registration.register_member(f"Mechanic for {driver_name}", "mechanic")
    crew.assign_role(mechanic.member_id, "mechanic")
    car = inventory.add_car(car_name)
    first_race = races.create_race("River Run", prize_money)
    races.enter_race(first_race.race_id, driver.member_id, car.car_id)
    results.record_result(first_race, [driver.member_id], damaged_car_ids=[car.car_id])

    second_race = races.create_race("Hill Chase", prize_money + 500)
    with pytest.raises(ValueError, match="race-ready"):
        races.enter_race(second_race.race_id, driver.member_id, car.car_id)

    garage.repair_car(car.car_id)
    races.enter_race(second_race.race_id, driver.member_id, car.car_id)
    assert car.assigned_driver_id == driver.member_id


@pytest.mark.parametrize(("prize_money", "ranking_points"), RESULT_CASES)
def test_results_update_cash_balance_and_rankings(
    prize_money: int,
    ranking_points: list[int],
) -> None:
    modules = build_modules()
    registration = modules["registration"]
    inventory = modules["inventory"]
    races = modules["races"]
    results = modules["results"]

    member_ids: list[int] = []
    for index, _points in enumerate(ranking_points, start=1):
        driver = registration.register_member(f"Finisher {index}", "driver")
        car = inventory.add_car(f"Result Car {index}")
        race = races.create_race("Results Cup", prize_money)
        races.enter_race(race.race_id, driver.member_id, car.car_id)
        member_ids.append(driver.member_id)

    target_race = races.races[max(races.races)]
    results.record_result(target_race, member_ids)

    assert inventory.cash_balance == prize_money
    assert results.rankings[member_ids[0]] == 10
    for member_id, points in zip(member_ids[1:], ranking_points[1:], strict=False):
        assert results.rankings[member_id] == points


@pytest.mark.parametrize("required_roles", MISSION_UNAVAILABLE_CASES)
def test_mission_cannot_start_when_required_role_is_unavailable(
    required_roles: list[str],
) -> None:
    modules = build_modules()
    registration = modules["registration"]
    crew = modules["crew"]
    missions = modules["missions"]

    for role in {"driver", "mechanic", "strategist", "navigator"}:
        member = registration.register_member(f"{role.title()} Member", role)
        if role in required_roles:
            crew.set_availability(member.member_id, False)

    mission = missions.create_mission("Blocked Mission", required_roles)

    with pytest.raises(ValueError, match="Required role unavailable"):
        missions.start_mission(mission.mission_id)


@pytest.mark.parametrize("required_roles", MISSION_AVAILABLE_CASES)
def test_mission_starts_when_all_required_roles_are_available(
    required_roles: list[str],
) -> None:
    modules = build_modules()
    registration = modules["registration"]
    missions = modules["missions"]

    for role in {"driver", "mechanic", "strategist", "navigator"}:
        registration.register_member(f"Available {role}", role)

    mission = missions.create_mission("Ready Mission", required_roles)
    missions.start_mission(mission.mission_id)

    assert mission.status == "ACTIVE"


@pytest.mark.parametrize(("income", "expense"), FINANCE_SUCCESS_CASES)
def test_finance_ledger_updates_inventory_cash(income: int, expense: int) -> None:
    modules = build_modules()
    inventory = modules["inventory"]
    finance = modules["finance"]

    finance.record_income("Sponsor payout", income)
    finance.record_expense("Tyre purchase", expense)

    assert inventory.cash_balance == income - expense
    assert finance.ledger == [("Sponsor payout", income), ("Tyre purchase", -expense)]


@pytest.mark.parametrize(("starting_cash", "expense"), FINANCE_INVALID_EXPENSE_CASES)
def test_finance_rejects_expense_above_available_cash(
    starting_cash: int,
    expense: int,
) -> None:
    modules = build_modules()
    inventory = modules["inventory"]
    finance = modules["finance"]

    inventory.add_cash(starting_cash)

    with pytest.raises(ValueError, match="Invalid cash spend"):
        finance.record_expense("Engine rebuild", expense)
