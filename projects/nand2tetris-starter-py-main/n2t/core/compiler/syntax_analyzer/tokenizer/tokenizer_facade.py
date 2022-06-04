from __future__ import annotations

from typing import Iterable, Iterator

from n2t.core.compiler.syntax_analyzer.tokenizer.token import Token, TokenType
from n2t.core.compiler.xml_symbols import XMLSymbols
from n2t.infra.io import FileFormat


class JackTokenizer:
    @classmethod
    def create(cls) -> JackTokenizer:
        return cls()

    def __init__(self) -> None:
        self.index = 0
        self.tokens: list[str] | None = None
        self.program: Iterable[str] | None = None

    def load_program(self, program: Iterable[str]) -> JackTokenizer:
        self.__init__()
        self.program = program
        return self

    def get_token(self) -> Token:
        if self.tokens is None:
            self.tokens = [token for token in self]

        return_token = self.tokens[self.index]

        return return_token

    def advance(self) -> None:
        self.index += 1

    def has_next(self) -> bool:
        if self.tokens is None:
            self.tokens = [token for token in self]

        return self.index + 1 < len(self.tokens)

    def __iter__(self) -> Iterator[Token]:
        assert self.program

        for line in self.program:
            yield from Token.get_tokens(line)


class JackTokenizerXmlPrinter:
    type_names_for_xml = {
        TokenType.int_const: "integerConstant",
        TokenType.identifier: "identifier",
        TokenType.keyword: "keyword",
        TokenType.string_const: "stringConstant",
        TokenType.symbol: "symbol",
    }

    def get_file_format(self) -> FileFormat:
        return FileFormat.xml

    def to_string(self, tokenizer: JackTokenizer) -> Iterable[str]:
        xml = list[str]()
        xml.append("<tokens>")

        for token in tokenizer:
            type = token.type
            value = token.value.get_value()
            value = value.lower() if token.type == TokenType.keyword else value

            if type == TokenType.symbol:
                value = XMLSymbols.get_xml_symbol(value)

            type_name = self.type_names_for_xml[type]

            xml.append(f"<{type_name}> {value} </{type_name}>")

        xml.append("</tokens>")
        return xml
