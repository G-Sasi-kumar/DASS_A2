"""Dice utilities for MoneyPoly."""

import random


class Dice:
    """Represents the pair of six-sided dice used in the game."""

    def __init__(self):
        self.die1 = 1
        self.die2 = 1
        self.doubles_streak = 0

    def roll(self):
        """Roll both dice, update streak state, and return the total."""
        self.die1 = random.randint(1, 6)
        self.die2 = random.randint(1, 6)
        if self.is_doubles():
            self.doubles_streak += 1
        else:
            self.doubles_streak = 0
        return self.die1 + self.die2

    def is_doubles(self):
        """Return True if both dice show the same value."""
        return self.die1 == self.die2

    def describe(self):
        """Return a human-readable description of the current dice."""
        doubles_tag = " (doubles)" if self.is_doubles() else ""
        return f"{self.die1} + {self.die2} = {self.die1 + self.die2}{doubles_tag}"

    def reset_streak(self):
        """Reset the doubles streak counter to zero."""
        self.doubles_streak = 0
