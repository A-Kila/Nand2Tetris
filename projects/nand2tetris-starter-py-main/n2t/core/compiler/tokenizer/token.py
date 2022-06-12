from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Protocol

SYMBOLS = {
    "{",
    "}",
    "(",
    ")",
    "[",
    "]",
    ".",
    ",",
    ";",
    "+",
    "-",
    "*",
    "/",
    "&",
    "|",
    "<",
    ">",
    "=",
    "~",
}

COMMENT_SYMBOLS = {"*", "/"}


class TokenValue(Protocol):
    def get_value(self) -> str:
        pass


class KeywordToken(Enum):
    class_token = "class"
    method_token = "method"
    function_token = "function"
    constructor_token = "constructor"
    int_token = "int"
    bool_token = "boolean"
    char_token = "char"
    void_token = "void"
    var_token = "var"
    static_token = "static"
    field_token = "field"
    let_token = "let"
    do_token = "do"
    if_token = "if"
    else_token = "else"
    while_token = "while"
    return_token = "return"
    true_token = "true"
    false_token = "false"
    null_token = "null"
    this_token = "this"

    @classmethod
    def contains(cls, item: str) -> bool:
        return any(x.value == item for x in cls)

    def get_value(self) -> str:
        return self.value


@dataclass
class BasicToken:
    value: str

    def get_value(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)


class TokenType(Enum):
    keyword = "KEYWORD"
    symbol = "SYMBOL"
    identifier = "IDENTIFIER"
    int_const = "INT_CONST"
    string_const = "STRING_CONST"
    comment = "COMMENT"
    one_line_comment = "ONE_LINE_COMMENT"


class TokenTypeGetHelper:
    token_is_string = False
    token_is_comment = False

    @classmethod
    def get_token_type(cls, string: str) -> TokenType:
        if string[0] == '"' or string[-1] == '"' or cls.token_is_string:
            cls.token_is_string = False if string[-1] == '"' else True
            return TokenType.string_const

        if string[0:2] == "//":
            return TokenType.one_line_comment

        if string[0:2] == "/*" or string[-2:] == "*/" or cls.token_is_comment:
            cls.token_is_comment = False if string[-2:] == "*/" else True
            return TokenType.comment

        if KeywordToken.contains(string):
            return TokenType.keyword

        if string in SYMBOLS:
            return TokenType.symbol

        if string.isnumeric():
            return TokenType.int_const

        return TokenType.identifier


class CommentCatcher:
    is_next_comment = False

    @classmethod
    def is_comment_in_word(cls, word: str) -> bool:
        from re import search

        if search(r"/\*", word):
            cls.is_next_comment = True

        if search(r"\*/", word):
            cls.is_next_comment = False

        return cls.is_next_comment or search(r"(//)|(/\*)|(\*/)", word) is not None


@dataclass(frozen=True)
class Token:
    value: TokenValue
    type: TokenType

    @classmethod
    def get_tokens(cls, string: str) -> Iterable[Token]:
        tokens: list[Token] = []
        typeGetter = TokenTypeGetHelper

        string_token = ""
        for word in cls.split(string):
            type = typeGetter.get_token_type(word)

            if type == TokenType.one_line_comment:
                break

            if type == TokenType.comment:
                continue

            if string_token != "" and type != TokenType.string_const:
                string_value = BasicToken(string_token[1:-1])  # strip qoutes
                tokens.append(cls(string_value, TokenType.string_const))
                string_token = ""

            if type == TokenType.keyword:
                keyword_value = KeywordToken(word)
                tokens.append(cls(keyword_value, type))
                continue

            if type == TokenType.string_const:
                string_token += word if string_token == "" else " " + word
                continue

            token_value = BasicToken(word)
            tokens.append(cls(token_value, type))

        return tokens

    @classmethod
    def split(cls, string: str) -> list[str]:
        tokens = []

        for word in string.split():
            token = ""

            for char in word:
                if char in SYMBOLS and not (
                    CommentCatcher.is_comment_in_word(word) and char in COMMENT_SYMBOLS
                ):
                    if token != "":
                        tokens.append(token)
                    tokens.append(char)
                    token = ""
                else:
                    token += char

            if token != "":
                tokens.append(token)

        return tokens
