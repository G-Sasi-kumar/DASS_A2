"""Main MoneyPoly game loop and mechanics."""

from moneypoly.config import (
    JAIL_FINE,
    AUCTION_MIN_INCREMENT,
    INCOME_TAX_AMOUNT,
    LUXURY_TAX_AMOUNT,
    MAX_TURNS,
    GO_SALARY,
)
from moneypoly.player import Player
from moneypoly.board import Board
from moneypoly.bank import Bank
from moneypoly.dice import Dice
from moneypoly.cards import CardDeck, CHANCE_CARDS, COMMUNITY_CHEST_CARDS
from moneypoly import ui


class Game:
    """Manages the full state and flow of a MoneyPoly game session."""

    def __init__(self, player_names):
        self.board = Board()
        self.bank = Bank()
        self.dice = Dice()
        self.players = [Player(name) for name in player_names]
        self.current_index = 0
        self.turn_number = 0
        self.running = True
        self.chance_deck = CardDeck(CHANCE_CARDS)
        self.community_deck = CardDeck(COMMUNITY_CHEST_CARDS)

    def current_player(self):
        """Return the Player whose turn it currently is."""
        return self.players[self.current_index]

    def advance_turn(self):
        """Move to the next player in the rotation."""
        self.current_index = (self.current_index + 1) % len(self.players)
        self.turn_number += 1

    def play_turn(self):
        """Execute one complete turn for the current player."""
        player = self.current_player()
        ui.print_banner(
            f"Turn {self.turn_number + 1}  |  {player.name}  |  ${player.balance}"
        )

        if player.in_jail:
            self._handle_jail_turn(player)
            self.advance_turn()
            return

        roll = self.dice.roll()
        print(f"  {player.name} rolled: {self.dice.describe()}")

        if self.dice.doubles_streak >= 3:
            print(f"  {player.name} rolled doubles three times in a row — go to jail!")
            player.go_to_jail()
            self.advance_turn()
            return

        self._move_and_resolve(player, roll)

        if self.dice.is_doubles():
            print(f"  Doubles! {player.name} rolls again.")
            return

        self.advance_turn()

    def _move_and_resolve(self, player, steps):
        """Move `player` by `steps` and trigger whatever tile they land on."""
        player.move(steps)
        position = player.position
        tile = self.board.get_tile_type(position)
        print(f"  {player.name} moved to position {position}  [{tile}]")

        if tile == "go_to_jail":
            player.go_to_jail()
            print(f"  {player.name} has been sent to Jail!")

        elif tile == "income_tax":
            player.deduct_money(INCOME_TAX_AMOUNT)
            self.bank.collect(INCOME_TAX_AMOUNT)
            print(f"  {player.name} paid income tax: ${INCOME_TAX_AMOUNT}.")

        elif tile == "luxury_tax":
            player.deduct_money(LUXURY_TAX_AMOUNT)
            self.bank.collect(LUXURY_TAX_AMOUNT)
            print(f"  {player.name} paid luxury tax: ${LUXURY_TAX_AMOUNT}.")

        elif tile == "free_parking":
            print(f"  {player.name} rests on Free Parking. Nothing happens.")

        elif tile == "chance":
            card = self.chance_deck.draw()
            self._apply_card(player, card)

        elif tile == "community_chest":
            card = self.community_deck.draw()
            self._apply_card(player, card)

        elif tile == "railroad":
            prop = self.board.get_property_at(position)
            if prop is not None:
                self._handle_property_tile(player, prop)

        elif tile == "property":
            prop = self.board.get_property_at(position)
            if prop is not None:
                self._handle_property_tile(player, prop)

        self._check_bankruptcy(player)

    def _handle_property_tile(self, player, prop):
        """Decide what to do when `player` lands on a property tile."""
        if prop.owner is None:
            print(f"  {prop.name} is unowned — asking price ${prop.price}.")
            try:
                choice = input("  Buy (b), Auction (a), or Skip (s)? ").strip().lower()
            except EOFError:
                choice = "s"
            if choice == "b":
                self.buy_property(player, prop)
            elif choice == "a":
                self.auction_property(prop)
            else:
                print(f"  {player.name} passes on {prop.name}.")
        elif prop.owner == player:
            print(f"  {player.name} owns {prop.name}. No rent due.")
        else:
            self.pay_rent(player, prop)

    def buy_property(self, player, prop):
        """Purchase `prop` on behalf of `player`."""
        if prop.owner is not None:
            print(f"  {prop.name} is already owned by {prop.owner.name}.")
            return False
        if player.balance < prop.price:
            print(f"  {player.name} cannot afford {prop.name} (${prop.price}).")
            return False
        player.deduct_money(prop.price)
        prop.owner = player
        player.add_property(prop)
        self.bank.collect(prop.price)
        print(f"  {player.name} purchased {prop.name} for ${prop.price}.")
        return True

    def pay_rent(self, player, prop):
        """Charge `player` rent and transfer it to the owner."""
        if prop.owner == player:
            return False
        if prop.is_mortgaged:
            print(f"  {prop.name} is mortgaged — no rent collected.")
            return False
        if prop.owner is None:
            return False

        rent = prop.get_rent()
        if player.balance < rent:
            return False
        player.deduct_money(rent)
        prop.owner.add_money(rent)
        print(f"  {player.name} paid ${rent} rent on {prop.name} to {prop.owner.name}.")
        return True

    def mortgage_property(self, player, prop):
        """Mortgage `prop` owned by `player` and credit them the payout."""
        if prop.owner != player:
            print(f"  {player.name} does not own {prop.name}.")
            return False
        payout = prop.mortgage()
        if payout == 0:
            print(f"  {prop.name} is already mortgaged.")
            return False
        player.add_money(payout)
        print(f"  {player.name} mortgaged {prop.name} and received ${payout}.")
        return True

    def unmortgage_property(self, player, prop):
        """Lift the mortgage on `prop`, charging the player the redemption cost."""
        if prop.owner != player:
            print(f"  {player.name} does not own {prop.name}.")
            return False
        cost = prop.unmortgage()
        if cost == 0:
            print(f"  {prop.name} is not mortgaged.")
            return False
        if player.balance < cost:
            print(f"  {player.name} cannot afford to unmortgage {prop.name} (${cost}).")
            return False
        player.deduct_money(cost)
        self.bank.collect(cost)
        print(f"  {player.name} unmortgaged {prop.name} for ${cost}.")
        return True

    def trade(self, seller, buyer, prop, cash_amount):
        """Execute a property trade between two players."""
        if prop.owner != seller:
            print(f"  Trade failed: {seller.name} does not own {prop.name}.")
            return False
        if buyer.balance < cash_amount:
            print(f"  Trade failed: {buyer.name} cannot afford ${cash_amount}.")
            return False

        buyer.deduct_money(cash_amount)
        prop.owner = buyer
        seller.remove_property(prop)
        buyer.add_property(prop)
        print(
            f"  Trade complete: {seller.name} sold {prop.name} "
            f"to {buyer.name} for ${cash_amount}."
        )
        return True

    def auction_property(self, prop):
        """Run an open auction for `prop` among all active players."""
        print(f"\n  [Auction] Bidding on {prop.name} (listed at ${prop.price})")
        highest_bid = 0
        highest_bidder = None

        for player in self.players:
            print(
                f"  {player.name}'s bid (balance: ${player.balance}, "
                f"current high: ${highest_bid}):"
            )
            bid = ui.safe_int_input("  Enter amount (0 to pass): ", default=0)
            if bid <= 0:
                print(f"  {player.name} passes.")
                continue
            min_required = highest_bid + AUCTION_MIN_INCREMENT
            if bid < min_required:
                print(f"  Bid too low — minimum raise is ${AUCTION_MIN_INCREMENT}.")
                continue
            if bid > player.balance:
                print(f"  {player.name} cannot afford ${bid}.")
                continue
            highest_bid = bid
            highest_bidder = player
            print(f"  {player.name} bids ${bid}.")

        if highest_bidder is not None:
            highest_bidder.deduct_money(highest_bid)
            prop.owner = highest_bidder
            highest_bidder.add_property(prop)
            self.bank.collect(highest_bid)
            print(
                f"  {highest_bidder.name} won {prop.name} "
                f"at auction for ${highest_bid}."
            )
        else:
            print(f"  No bids placed. {prop.name} remains unowned.")

    def _handle_jail_turn(self, player):
        """Process a jailed player's turn — offer to pay fine or use card."""
        print(f"  {player.name} is in jail (turn {player.jail_turns + 1}/3).")

        if player.get_out_of_jail_cards > 0:
            if ui.confirm("  Use your Get Out of Jail Free card? (y/n): "):
                player.get_out_of_jail_cards -= 1
                player.in_jail = False
                player.jail_turns = 0
                print(f"  {player.name} used a Get Out of Jail Free card!")
                roll = self.dice.roll()
                print(f"  {player.name} rolled: {self.dice.describe()}")
                self._move_and_resolve(player, roll)
                return

        if ui.confirm(f"  Pay ${JAIL_FINE} fine to leave jail? (y/n): "):
            if player.balance < JAIL_FINE:
                print(f"  {player.name} cannot afford the jail fine.")
                player.jail_turns += 1
                return
            player.deduct_money(JAIL_FINE)
            self.bank.collect(JAIL_FINE)
            player.in_jail = False
            player.jail_turns = 0
            print(f"  {player.name} paid the ${JAIL_FINE} fine and is released.")
            roll = self.dice.roll()
            print(f"  {player.name} rolled: {self.dice.describe()}")
            self._move_and_resolve(player, roll)
            return

        player.jail_turns += 1
        if player.jail_turns >= 3:
            print(f"  {player.name} must leave jail. Paying mandatory ${JAIL_FINE} fine.")
            player.deduct_money(JAIL_FINE)
            self.bank.collect(JAIL_FINE)
            player.in_jail = False
            player.jail_turns = 0
            roll = self.dice.roll()
            print(f"  {player.name} rolled: {self.dice.describe()}")
            self._move_and_resolve(player, roll)

    def _apply_card(self, player, card):
        """Apply the effect of a drawn Chance or Community Chest card."""
        if card is None:
            return
        print(f"  Card drawn: \"{card['description']}\"")
        action = card["action"]
        value = card["value"]

        if action == "collect":
            amount = self.bank.pay_out(value)
            player.add_money(amount)

        elif action == "pay":
            player.deduct_money(value)
            self.bank.collect(value)

        elif action == "jail":
            player.go_to_jail()
            print(f"  {player.name} has been sent to Jail!")

        elif action == "jail_free":
            player.get_out_of_jail_cards += 1
            print(f"  {player.name} now holds a Get Out of Jail Free card.")

        elif action == "move_to":
            old_pos = player.position
            player.position = value
            if value < old_pos:
                player.add_money(GO_SALARY)
                print(f"  {player.name} passed Go and collected ${GO_SALARY}.")
            tile = self.board.get_tile_type(value)
            if tile == "property":
                prop = self.board.get_property_at(value)
                if prop:
                    self._handle_property_tile(player, prop)

        elif action == "birthday":
            for other in self.players:
                if other != player and other.balance >= value:
                    other.deduct_money(value)
                    player.add_money(value)

        elif action == "collect_from_all":
            for other in self.players:
                if other != player and other.balance >= value:
                    other.deduct_money(value)
                    player.add_money(value)

    def _check_bankruptcy(self, player):
        """Eliminate `player` from the game if they are bankrupt."""
        if player.is_bankrupt():
            print(f"\n  *** {player.name} is bankrupt and has been eliminated! ***")
            player.is_eliminated = True
            for prop in list(player.properties):
                prop.owner = None
                prop.is_mortgaged = False
            player.properties.clear()
            if player in self.players:
                self.players.remove(player)
            if self.players and self.current_index >= len(self.players):
                self.current_index = 0

    def find_winner(self):
        """Return the player with the highest net worth."""
        if not self.players:
            return None
        return max(self.players, key=lambda player: player.net_worth())

    def run(self):
        """Run the game loop until only one player remains or turns run out."""
        ui.print_banner("Welcome to MoneyPoly!")
        print()
        for player in self.players:
            print(f"  {player.name} starts with ${player.balance}.")

        while self.running and self.turn_number < MAX_TURNS:
            if len(self.players) <= 1:
                break
            self.play_turn()
            ui.print_standings(self.players)
            print()

        winner = self.find_winner()
        if winner:
            ui.print_banner("GAME OVER")
            print(f"\n  {winner.name} wins with a net worth of ${winner.net_worth()}!\n")
        else:
            print("\n  The game ended with no players remaining.")
