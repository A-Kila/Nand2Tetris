from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from n2t.core.hack_simulator import HackSimulator as DefaultHackSimulator
from n2t.infra.io import File, FileFormat


@dataclass
class HackSimProgram:
    path: Path
    hack_simulator: HackSimulator = field(default_factory=DefaultHackSimulator.create)

    @classmethod
    def load_from(cls, file_name: str) -> HackSimProgram:
        return cls(Path(file_name))

    def __post_init__(self) -> None:
        FileFormat.hack.validate(self.path)

    def simulate(self) -> None:
        out_file = File(FileFormat.out.convert(self.path))
        out_file.save(self.hack_simulator.simulate(self))

    def __iter__(self) -> Iterator[str]:
        yield from File(self.path).load()


class HackSimulator(Protocol):
    def simulate(self, hack: Iterable[str]) -> Iterable[str]:
        pass
