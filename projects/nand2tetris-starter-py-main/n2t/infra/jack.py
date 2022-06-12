from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Protocol

from n2t.core.compiler.parser.parser_facade import JackCompiler
from n2t.core.compiler.tokenizer.token import Token
from n2t.core.compiler.tokenizer.tokenizer_facade import (
    JackTokenizer as DefaultJackTokenizer,
    JackTokenizerXmlPrinter,
)
from n2t.infra.io import File, FileFormat


class JackTokenizer(Protocol):
    def load_program(self, program: Iterator[str]) -> JackTokenizer:
        pass

    def get_token(self) -> Token:
        pass

    def advance(self) -> Token:
        pass

    def has_next(self) -> bool:
        pass

    def __iter__(self) -> Iterator[Token]:
        pass


class JackTokenizerPrinter(Protocol):
    def get_file_format(self) -> FileFormat:
        pass

    def to_string(self, tokenizer: JackTokenizer) -> Iterable[str]:
        pass


class JackCompilationEngine(Protocol):
    def get_file_format(self) -> FileFormat:
        pass

    def compile(self, tokenizer: JackTokenizer) -> Iterable[str]:
        pass


@dataclass
class JackProgram:
    base_path: Path
    file_paths: list[Path] = field(default_factory=list)
    tokenizer: JackTokenizer = field(default_factory=DefaultJackTokenizer.create)
    tokenizer_printer: JackTokenizerPrinter = field(
        default_factory=JackTokenizerXmlPrinter
    )
    compiler: JackCompilationEngine = field(default_factory=JackCompiler)

    @classmethod
    def load_from(cls, file_or_directory_name: str) -> JackProgram:
        return cls(Path(file_or_directory_name))

    def __post_init__(self) -> None:
        if self.base_path.suffix == "":
            for file_path in self.base_path.iterdir():
                if FileFormat.jack.is_format(file_path):
                    self.file_paths.append(file_path)
        else:
            if FileFormat.jack.is_format(self.base_path):
                self.file_paths.append(self.base_path)

    def compile(self) -> None:
        for file_path in self.file_paths:
            # self.__tokenizer_out(file_path)
            self.__parser_out(file_path)

    def __tokenizer_out(self, file_path: Path) -> None:
        jack_path = self.tokenizer_printer.get_file_format().convert(file_path)
        filename = jack_path.stem + "T"
        xml_path = File(jack_path.with_stem(filename).with_suffix(".xml"))
        xml_path.save(
            self.tokenizer_printer.to_string(
                self.tokenizer.load_program(self.__iter_file(file_path))
            )
        )

    def __parser_out(self, file_path: Path) -> None:
        xml_file = File(self.compiler.get_file_format().convert(file_path))
        xml_file.save(
            self.compiler.compile(
                self.tokenizer.load_program(self.__iter_file(file_path))
            )
        )

    def __iter_file(self, file_path: Path) -> Iterator[str]:
        yield from File(file_path).load()
