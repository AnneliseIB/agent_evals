#!/bin/bash
set -euo pipefail

cat > /app/river_sim.py <<'PY'
class River:
    """A class representing a river ecosystem with fish and bears."""
    fish: int
    bears: int

    def __init__(self, fish: int, bears: int):
        """Initialize the River with a given number of fish and bears."""
        self.fish = fish
        self.bears = bears

    def one_day(self):
        """Simulate one day in the river ecosystem."""
        self.fish += (self.fish // 2) * 3
        self.fish -= self.bears
        self.bears += self.bears // 2


def main():
    """Run the river simulation for one day and print the results."""
    river: River = River(10, 10)
    river.one_day()
    print(f"Fish: {river.fish}, Bears: {river.bears}")
PY