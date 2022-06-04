from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class FileFormat(Enum):
    hack = ".hack"
    asm = ".asm"
    vm = ".vm"
    jack = ".jack"
    xml = ".xml"

    def validate(self, path: Path) -> None:
        assert path.suffix == self.value

    def is_format(self, path: Path) -> bool:
        return path.suffix == self.value

    def convert(self, path: Path) -> Path:
        return path.with_suffix(self.value)


@dataclass(frozen=True)
class File:
    path: Path

    def load(self) -> Iterable[str]:
        with self.path.open("r", newline="") as file:
            yield from (line.strip() for line in file if line)

    def save(self, lines: Iterable[str]) -> None:
        with self.path.open("w", newline="") as file:
            for line in lines:
                file.write(f"{line}\r\n")

    def append(self, lines: Iterable[str]) -> None:
        with self.path.open("a", newline="") as file:
            for line in lines:
                file.write(f"{line}\n")

    def clear(self) -> File:
        self.path.open("w", newline="").close()
        return self


def remove_files(pattern: str) -> None:
    for file in glob.glob(pattern):
        os.remove(file)
