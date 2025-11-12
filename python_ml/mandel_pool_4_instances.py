#!/usr/bin/env python3
"""
MANDEL POOL GENERATOR - 4 SEPARATE INSTANCES
=============================================

Split the 4,457,400 combinations into 4 separate generators:

Instance 1: Combinations 0 - 1,114,349 (25%)
Instance 2: Combinations 1,114,350 - 2,228,699 (25%)
Instance 3: Combinations 2,228,700 - 3,343,049 (25%)
Instance 4: Combinations 3,343,050 - 4,457,399 (25%)

Each instance can be run independently in parallel or sequentially.
"""

import sys
from pathlib import Path
from itertools import combinations, islice
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

TOTAL_COMBINATIONS = 4457400
INSTANCES = 4
COMBINATIONS_PER_INSTANCE = TOTAL_COMBINATIONS // INSTANCES


class MandelPoolGeneratorInstance:
    """
    One instance of the pool generator handling a specific range of combinations
    """

    def __init__(self, instance_num: int):
        """
        Initialize pool generator instance

        Args:
            instance_num: Instance number (1-4)
        """
        if instance_num < 1 or instance_num > INSTANCES:
            raise ValueError(f"instance_num must be between 1 and {INSTANCES}")

        self.instance_num = instance_num
        self.start_idx = (instance_num - 1) * COMBINATIONS_PER_INSTANCE

        # Last instance gets any remainder
        if instance_num == INSTANCES:
            self.end_idx = TOTAL_COMBINATIONS
        else:
            self.end_idx = instance_num * COMBINATIONS_PER_INSTANCE

        self.total_combinations = self.end_idx - self.start_idx

    def generate_pool(self):
        """
        Generate all combinations for this instance

        Yields:
            List[int]: Each combination (14 numbers from 1-25)
        """
        # Generate all combinations
        all_combos = combinations(range(1, 26), 14)

        # Skip to start_idx
        if self.start_idx > 0:
            all_combos = islice(all_combos, self.start_idx, None)

        # Yield only this instance's combinations
        for combo in islice(all_combos, self.total_combinations):
            yield list(combo)

    def info(self):
        """Print information about this instance"""
        print(f"Instance {self.instance_num}/{INSTANCES}")
        print(f"  Range: {self.start_idx:,} to {self.end_idx-1:,}")
        print(f"  Total: {self.total_combinations:,} combinations")
        print(f"  Percentage: {(self.total_combinations/TOTAL_COMBINATIONS)*100:.1f}%")


# Create 4 instances
def create_instance_1():
    """Instance 1: Combinations 0 - 1,114,349"""
    return MandelPoolGeneratorInstance(1)


def create_instance_2():
    """Instance 2: Combinations 1,114,350 - 2,228,699"""
    return MandelPoolGeneratorInstance(2)


def create_instance_3():
    """Instance 3: Combinations 2,228,700 - 3,343,049"""
    return MandelPoolGeneratorInstance(3)


def create_instance_4():
    """Instance 4: Combinations 3,343,050 - 4,457,399"""
    return MandelPoolGeneratorInstance(4)


if __name__ == '__main__':
    print("=" * 80)
    print("MANDEL POOL GENERATOR - 4 INSTANCES")
    print("=" * 80)
    print()

    # Show all instances
    for i in range(1, INSTANCES + 1):
        instance = MandelPoolGeneratorInstance(i)
        instance.info()
        print()

    print("=" * 80)
    print("USAGE:")
    print("=" * 80)
    print()
    print("# Import and create instance")
    print("from mandel_pool_4_instances import create_instance_1")
    print()
    print("# Generate combinations for instance 1")
    print("instance = create_instance_1()")
    print("for combination in instance.generate_pool():")
    print("    score = model._calculate_score(combination)")
    print("    # ... process combination")
    print()
    print("# Or use directly")
    print("from mandel_pool_4_instances import MandelPoolGeneratorInstance")
    print("instance = MandelPoolGeneratorInstance(1)  # 1, 2, 3, or 4")
    print()
