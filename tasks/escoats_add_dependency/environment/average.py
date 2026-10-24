import numpy as np


def calculate_average(numbers: list[float]) -> float:
    """Calculate the average of a list of numbers."""
    return float(np.mean(numbers))


if __name__ == "__main__":
    print(calculate_average([1, 2, 3]))
