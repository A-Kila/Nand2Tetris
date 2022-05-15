from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from n2t.core.vm_translator.facade import VmTranslator as DefaultVmTranslator
from n2t.infra.io import File, FileFormat


class VmTranslator(Protocol):
    def translate(self, file_name: str, vm_code: Iterable[str]) -> Iterable[str]:
        pass

    def bootstrap(self) -> Iterable[str]:
        pass


@dataclass
class VmProgram:
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
        if self.base_path.suffix == "":
            out_file_path = self.base_path / self.base_path.stem
            assembly_file = File(FileFormat.asm.convert(out_file_path))
            assembly_file.clear().append(self.vm_translator.bootstrap())

            for in_file_path in self.file_paths:
                assembly_file.append(
                    self.vm_translator.translate(
                        in_file_path.stem, self.__iter_file(in_file_path)
                    )
                )

        else:
            file_path = self.file_paths[0]
            assembly_file = File(FileFormat.asm.convert(file_path))
            assembly_file.save(
                self.vm_translator.translate(
                    file_path.stem, self.__iter_file(file_path)
                )
            )

    def __iter_file(self, file_path: Path) -> Iterator[str]:
        yield from File(file_path).load()
