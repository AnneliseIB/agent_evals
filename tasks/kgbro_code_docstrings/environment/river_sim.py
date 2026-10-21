class River:
    fish: int
    bears: int

    def __init__(self, fish: int, bears: int):
        self.fish = fish
        self.bears = bears

    def one_day(self):
        self.fish += (self.fish // 2) * 3
        self.fish -= self.bears
        self.bears += self.bears // 2

def main():
    river: River = River(10, 10)
    river.one_day()
    print(f"Fish: {river.fish}, Bears: {river.bears}")
