from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random


@dataclass
class ShuffleResult:
    original_order: List[str]
    shuffled_order: List[str]
    vars: Dict[str, str]
    seed: Optional[int] = None

    def __repr__(self) -> str:
        return (
            f"ShuffleResult(keys={len(self.original_order)}, "
            f"seed={self.seed})"
        )

    @property
    def has_changes(self) -> bool:
        return self.original_order != self.shuffled_order

    @property
    def changed_positions(self) -> int:
        return sum(
            1 for a, b in zip(self.original_order, self.shuffled_order) if a != b
        )


class EnvShuffler:
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed

    def shuffle(self, vars: Dict[str, str]) -> ShuffleResult:
        original_order = list(vars.keys())
        keys = list(vars.keys())
        rng = random.Random(self.seed)
        rng.shuffle(keys)
        shuffled_vars = {k: vars[k] for k in keys}
        return ShuffleResult(
            original_order=original_order,
            shuffled_order=keys,
            vars=shuffled_vars,
            seed=self.seed,
        )

    def restore(self, result: ShuffleResult) -> Dict[str, str]:
        return {k: result.vars[k] for k in result.original_order}
