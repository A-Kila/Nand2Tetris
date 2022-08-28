from __future__ import annotations

from typing import Iterable


class HackSimulator:
    @classmethod
    def create(cls) -> HackSimulator:
        return cls()

    def simulate(self, hack: Iterable[str], cycles: int) -> Iterable[str]:
        pass
