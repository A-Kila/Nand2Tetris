from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from n2t.core.hack_simulator import HackSimulator as DefaultHackSimulator
from n2t.infra.io import File, FileFormat


class RamPrinter:
    def print(self, ram: RamI) -> Iterable[str]:
        result = []

        for i in range(ram.get_size()):
            is_used, value = ram.get(i)

            line = f"Ram[{i}]: {'{0:016b}'.format(value) if is_used else ''}"
            result.append(line)

        return result


@dataclass
class HackSimProgram:
    path: Path
    cycles: int
    hack_simulator: HackSimulator = field(default_factory=DefaultHackSimulator.create)
    ram_printer: RamPrinter = field(default_factory=RamPrinter)

    @classmethod
    def load_from(cls, file_name: str, cycles: int) -> HackSimProgram:
        return cls(Path(file_name), cycles)

    def __post_init__(self) -> None:
        FileFormat.hack.validate(self.path)

    def simulate(self) -> None:
        out_file = File(FileFormat.out.convert(self.path))
        out_file.save(
            self.ram_printer.print(
                self.hack_simulator.simulate(list(self), self.cycles)
            )
        )

    def __iter__(self) -> Iterator[str]:
        yield from File(self.path).load()


class RamI(Protocol):
    def get_size(self) -> int:
        pass

    def set(self, address: int, value: int) -> None:
        pass

    def get(self, address: int) -> tuple[bool, int]:
        pass


class HackSimulator(Protocol):
    def simulate(self, hack: list[str], cycles: int) -> RamI:
        pass
