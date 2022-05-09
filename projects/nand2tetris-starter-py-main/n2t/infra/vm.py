from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from n2t.core.vm_translator.facade import VmTranslator as DefaultVmTranslator
from n2t.infra.io import File, FileFormat


class VmTranslator(Protocol):
    def translate(self, vm_code: Iterable[str]) -> Iterable[str]:
        pass


@dataclass
class VmProgram:  # TODO: your work for Projects 8 starts here
    base_path: Path
    file_paths: list[Path] = field(default_factory=list)
    vm_translator: VmTranslator = field(default_factory=DefaultVmTranslator.create)

    @classmethod
    def load_from(cls, file_or_directory_name: str) -> VmProgram:
        return cls(Path(file_or_directory_name))

    def __post_init__(self) -> None:
        if self.base_path.suffix == "":
            for file_path in self.base_path.iterdir():
                if FileFormat.vm.is_format(file_path):
                    self.file_paths.append(file_path)
        else:
            if FileFormat.vm.is_format(self.base_path):
                self.file_paths.append(self.base_path)

    def translate(self) -> None:
        for file_path in self.file_paths:
            assembly_file = File(FileFormat.asm.convert(file_path))
            assembly_file.save(
                self.vm_translator.translate(self.__iter_file(file_path))
            )

    def __iter_file(self, file_path: Path) -> Iterator[str]:
        yield from File(file_path).load()
