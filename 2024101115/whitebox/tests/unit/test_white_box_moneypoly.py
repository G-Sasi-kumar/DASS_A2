"""White-box tests for core MoneyPoly game mechanics."""

# pylint: disable=duplicate-code

from __future__ import annotations

from moneypoly.bank import Bank
from moneypoly.board import Board
from moneypoly.dice import Dice
from moneypoly.game import Game
from moneypoly.player import Player


def _make_game() -> Game:
    return Game(["Alice", "Bob"])


def test_player_move_collects_go_salary_when_passing_go() -> None:
    player = Player("A", balance=1000)
    player.position = 39
    player.move(2)
    assert player.position == 1
    assert player.balance == 1200


def test_player_move_without_wrapping_no_salary() -> None:
    player = Player("A", balance=1000)
    player.position = 5
    player.move(3)
    assert player.position == 8
    assert player.balance == 1000


def test_property_group_all_owned_by_requires_full_group() -> None:
    board = Board()
    brown_group = board.groups["brown"]
    owner = Player("Owner")
    assert len(brown_group.properties) >= 2
    first = brown_group.properties[0]
    second = brown_group.properties[1]
    first.owner = owner
    second.owner = None
    assert brown_group.all_owned_by(owner) is False
    second.owner = owner
    assert brown_group.all_owned_by(owner) is True


def test_buy_property_allows_exact_balance() -> None:
    game = _make_game()
    player = game.players[0]
    prop = game.board.properties[0]
    player.balance = prop.price
    assert game.buy_property(player, prop) is True
    assert prop.owner == player
    assert prop in player.properties
    assert player.balance == 0


def test_buy_property_rejects_when_insufficient() -> None:
    game = _make_game()
    player = game.players[0]
    prop = game.board.properties[0]
    player.balance = prop.price - 1
    assert game.buy_property(player, prop) is False
    assert prop.owner is None


def test_pay_rent_transfers_money_to_owner() -> None:
    game = _make_game()
    owner = game.players[0]
    renter = game.players[1]
    prop = game.board.groups["brown"].properties[0]
    prop.owner = owner
    owner_start = owner.balance
    renter_start = renter.balance

    game.pay_rent(renter, prop)

    assert renter.balance == renter_start - prop.get_rent()
    assert owner.balance == owner_start + prop.get_rent()


def test_pay_rent_skips_mortgaged_property() -> None:
    game = _make_game()
    owner = game.players[0]
    renter = game.players[1]
    prop = game.board.properties[0]
    prop.owner = owner
    prop.is_mortgaged = True

    owner_start = owner.balance
    renter_start = renter.balance
    game.pay_rent(renter, prop)

    assert owner.balance == owner_start
    assert renter.balance == renter_start


def test_find_winner_returns_highest_net_worth() -> None:
    game = _make_game()
    game.players[0].balance = 100
    game.players[1].balance = 500
    assert game.find_winner() == game.players[1]


def test_dice_roll_range_includes_six() -> None:
    dice = Dice()
    for _ in range(200):
        total = dice.roll()
        assert 2 <= total <= 12
        assert 1 <= dice.die1 <= 6
        assert 1 <= dice.die2 <= 6


def test_bank_collect_ignores_negative_amount() -> None:
    bank = Bank()
    before = bank.get_balance()
    bank.collect(-50)
    assert bank.get_balance() == before


def test_bank_loan_reduces_bank_balance_and_credits_player() -> None:
    bank = Bank()
    player = Player("Borrower", balance=100)
    before = bank.get_balance()
    bank.give_loan(player, 200)
    assert player.balance == 300
    assert bank.get_balance() == before - 200


def test_bankruptcy_removes_player_and_resets_properties() -> None:
    game = _make_game()
    bankrupt = game.players[0]
    prop = game.board.properties[0]
    prop.owner = bankrupt
    bankrupt.properties.append(prop)
    bankrupt.balance = 0

    game._check_bankruptcy(bankrupt)  # pylint: disable=protected-access

    assert bankrupt.is_eliminated is True
    assert bankrupt not in game.players
    assert prop.owner is None
    assert prop.is_mortgaged is False


def test_monopoly_rent_doubles_for_complete_group() -> None:
    game = _make_game()
    owner = game.players[0]
    brown = game.board.groups["brown"].properties
    for prop in brown:
        prop.owner = owner
    assert brown[0].get_rent() == brown[0].base_rent * 2


def test_package_imports_resolve_from_project_root() -> None:
    game = _make_game()
    assert game.current_player().name == "Alice"
