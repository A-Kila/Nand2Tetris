from __future__ import annotations
from dataclasses import dataclass, field

from typing import Iterable


@dataclass
class Registers:
    PC: int = 0
    D: int = 0
    A: int = 0
    M: int = 0


@dataclass
class Ram:
    size: int = 2**15
    values: dict[int, int] = field(default_factory=lambda: {})

    def set(self, address: int, value: int) -> None:
        assert address < self.size
        
        self.values[address] = value

    def get(self, address: int) -> int:
        assert address < self.size

        return self.values.get(address, 0)


@dataclass
class HackSimulator:
    registers: Registers = field(default_factory=Registers)
    ram: Ram = field(default_factory=Ram)

    @classmethod
    def create(cls) -> HackSimulator:
        return cls()

    def simulate(self, hack: Iterable[str], cycles: int) -> Iterable[str]:
        pass
