"""Trial schedule and geometry definitions for the target-hitting activity."""

import random


TARGET_DIAMETERS = {"Small": 15, "Medium": 30, "Large": 50}
TARGET_DISTANCES = {"Near": 100, "Medium": 250, "Far": 400}


def make_target_schedule(seed):
    """Return one practice trial followed by three shuffled trials per condition."""
    conditions = [
        (size, distance)
        for size in TARGET_DIAMETERS
        for distance in TARGET_DISTANCES
        for _ in range(3)
    ]
    random.Random(seed).shuffle(conditions)
    return [("Medium", "Near", True)] + [
        (size, distance, False) for size, distance in conditions
    ]
