from dataclasses import dataclass
from typing import Iterable

from n2t.core.compiler.syntax_analyzer.tokenizer.token import (
    KeywordToken,
    Token,
    TokenType,
)
from n2t.core.compiler.syntax_analyzer.tokenizer.tokenizer_facade import JackTokenizer
from n2t.core.compiler.xml_symbols import XMLSymbols


@dataclass
class JackXmlCompiler:
    tokenizer: JackTokenizer

    binary_operations = "+-*/&|<>="
    unary_operations = "-~"
    keyword_constants = {
        KeywordToken.true_token,
        KeywordToken.false_token,
        KeywordToken.null_token,
        KeywordToken.this_token,
    }

    def compile_class(self) -> Iterable[str]:
        xml = ["<class>"]

        xml.append(self.__compile_keyword({KeywordToken.class_token}))
        self.__tokenizer_advance()

        xml.append(self.__compile_identifier())
        self.__tokenizer_advance()

        xml.append(self.__compile_symbol("{"))
        self.__tokenizer_advance()

        while self.tokenizer.get_token().type == TokenType.keyword and (
            self.tokenizer.get_token().value == KeywordToken.static_token
            or self.tokenizer.get_token().value == KeywordToken.field_token
        ):
            xml.extend(self.__add_tabs(self.compile_class_var_dec()))
            self.__tokenizer_advance()

        while self.tokenizer.get_token().type == TokenType.keyword and (
            self.tokenizer.get_token().value == KeywordToken.constructor_token
            or self.tokenizer.get_token().value == KeywordToken.function_token
            or self.tokenizer.get_token().value == KeywordToken.method_token
        ):
            xml.extend(self.__add_tabs(self.compile_subroutine_dec()))
            self.__tokenizer_advance()

        xml.append(self.__compile_symbol("}"))
        assert not self.tokenizer.has_next()

        xml.append("</class>")
        return xml

    def compile_class_var_dec(self) -> Iterable[str]:
        xml = ["<classVarDec>"]

        xml.append(
            self.__compile_keyword(
                {KeywordToken.static_token, KeywordToken.field_token}
            )
        )
        self.__tokenizer_advance()

        xml.extend(self.compile_type())
        self.__tokenizer_advance()

        xml.append(self.__compile_identifier())
        self.__tokenizer_advance()

        while (
            self.tokenizer.get_token().type == TokenType.symbol
            and self.tokenizer.get_token().value.get_value() == ","
        ):
            xml.append(self.__compile_symbol(","))
            self.tokenizer.advance()

            xml.append(self.__compile_identifier())
            self.tokenizer.advance()

        xml.append(self.__compile_symbol(";"))

        xml.append("</classVarDec>")
        return xml

    def compile_type(self) -> Iterable[str]:
        xml = []

        type_token = self.tokenizer.get_token()
        assert (
            type_token.type == TokenType.keyword
            or type_token.type == TokenType.identifier
        )

        if type_token.type == TokenType.keyword:
            xml.append(
                self.__compile_keyword(
                    {
                        KeywordToken.int_token,
                        KeywordToken.char_token,
                        KeywordToken.bool_token,
                    }
                )
            )

        else:
            xml.append(self.__compile_identifier())

        return xml

    def compile_subroutine_dec(self) -> Iterable[str]:
        xml = ["<subroutineDec>"]

        xml.append(
            self.__compile_keyword(
                {
                    KeywordToken.constructor_token,
                    KeywordToken.function_token,
                    KeywordToken.method_token,
                }
            )
        )
        self.__tokenizer_advance()

        return_type = self.tokenizer.get_token()
        if return_type.value == KeywordToken.void_token:
            xml.append(self.__compile_keyword({KeywordToken.void_token}))
            self.__tokenizer_advance()

        else:
            xml.extend(self.compile_type())
            self.__tokenizer_advance()

        xml.append(self.__compile_identifier())
        self.__tokenizer_advance()

        xml.append(self.__compile_symbol("("))
        self.__tokenizer_advance()

        # token advance happend inside function
        xml.extend(self.__add_tabs(self.compile_parameter_list()))

        xml.append(self.__compile_symbol(")"))
        self.__tokenizer_advance()

        xml.extend(self.__add_tabs(self.compile_subroutine_body()))

        xml.append("</subroutineDec>")
        return xml

    def compile_parameter_list(self) -> Iterable[str]:
        xml = ["<parameterList>"]

        token = self.tokenizer.get_token()
        if token.type == TokenType.keyword or token.type == TokenType.identifier:
            xml.extend(self.compile_type())
            self.__tokenizer_advance()

            xml.append(self.__compile_identifier())
            self.__tokenizer_advance()

            while self.tokenizer.get_token().value.get_value() == ",":
                xml.append(self.__compile_symbol(","))
                self.__tokenizer_advance()

                xml.extend(self.compile_type())
                self.__tokenizer_advance()

                xml.append(self.__compile_identifier())
                self.__tokenizer_advance()

        xml.append("</parameterList>")
        return xml

    def compile_subroutine_body(self) -> Iterable[str]:
        xml = ["<subroutineBody>"]

        xml.append(self.__compile_symbol("{"))
        self.__tokenizer_advance()

        while self.tokenizer.get_token().value == KeywordToken.var_token:
            xml.extend(self.__add_tabs(self.compile_var_dec()))
            self.__tokenizer_advance()

        xml.extend(self.__add_tabs(self.compile_statements()))

        xml.append(self.__compile_symbol("}"))

        xml.append("</subroutineBody>")
        return xml

    def compile_var_dec(self) -> Iterable[str]:
        xml = ["<varDec>"]

        xml.append(self.__compile_keyword({KeywordToken.var_token}))
        self.__tokenizer_advance()

        xml.extend(self.compile_type())
        self.__tokenizer_advance()

        xml.append(self.__compile_identifier())
        self.__tokenizer_advance()

        while self.tokenizer.get_token().value.get_value() == ",":
            xml.append(self.__compile_symbol(","))
            self.__tokenizer_advance()

            xml.append(self.__compile_identifier())
            self.__tokenizer_advance()

        xml.append(self.__compile_symbol(";"))

        xml.append("</varDec>")
        return xml

    def compile_statements(self) -> Iterable[str]:
        xml = ["<statements>"]

        while self.tokenizer.get_token().value in {
            KeywordToken.let_token,
            KeywordToken.if_token,
            KeywordToken.while_token,
            KeywordToken.do_token,
            KeywordToken.return_token,
        }:
            value = self.tokenizer.get_token().value

            if value == KeywordToken.let_token:
                xml.extend(self.__add_tabs(self.compile_let()))
                self.__tokenizer_advance()

            if value == KeywordToken.if_token:
                xml.extend(self.__add_tabs(self.compile_if()))

            if value == KeywordToken.while_token:
                xml.extend(self.__add_tabs(self.compile_while()))
                self.__tokenizer_advance()

            if value == KeywordToken.do_token:
                xml.extend(self.__add_tabs(self.compile_do()))
                self.__tokenizer_advance()

            if value == KeywordToken.return_token:
                xml.extend(self.__add_tabs(self.compile_return()))
                self.__tokenizer_advance()

        xml.append("</statements>")
        return xml

    def compile_let(self) -> Iterable[str]:
        xml = ["<letStatement>"]

        xml.append(self.__compile_keyword({KeywordToken.let_token}))
        self.__tokenizer_advance()

        xml.append(self.__compile_identifier())
        self.__tokenizer_advance()

        if self.tokenizer.get_token().value.get_value() == "[":
            xml.append(self.__compile_symbol("["))
            self.__tokenizer_advance()

            xml.extend(self.__add_tabs(self.compile_expression()))

            xml.append(self.__compile_symbol("]"))
            self.__tokenizer_advance()

        xml.append(self.__compile_symbol("="))
        self.__tokenizer_advance()

        xml.extend(self.__add_tabs(self.compile_expression()))

        xml.append(self.__compile_symbol(";"))

        xml.append("</letStatement>")
        return xml

    def compile_if(self) -> Iterable[str]:
        xml = ["<ifStatement>"]

        xml.append(self.__compile_keyword({KeywordToken.if_token}))
        self.__tokenizer_advance()

        xml.append(self.__compile_symbol("("))
        self.__tokenizer_advance()

        xml.extend(self.__add_tabs(self.compile_expression()))

        xml.append(self.__compile_symbol(")"))
        self.__tokenizer_advance()

        xml.append(self.__compile_symbol("{"))
        self.__tokenizer_advance()

        xml.extend(self.__add_tabs(self.compile_statements()))

        xml.append(self.__compile_symbol("}"))
        self.__tokenizer_advance()

        if self.tokenizer.get_token().value == KeywordToken.else_token:
            xml.append(self.__compile_keyword({KeywordToken.else_token}))
            self.__tokenizer_advance()

            xml.append(self.__compile_symbol("{"))
            self.__tokenizer_advance()

            xml.extend(self.__add_tabs(self.compile_statements()))

            xml.append(self.__compile_symbol("}"))
            self.__tokenizer_advance()

        xml.append("</ifStatement>")
        return xml

    def compile_while(self) -> Iterable[str]:
        xml = ["<whileStatement>"]

        xml.append(self.__compile_keyword({KeywordToken.while_token}))
        self.__tokenizer_advance()

        xml.append(self.__compile_symbol("("))
        self.__tokenizer_advance()

        xml.extend(self.__add_tabs(self.compile_expression()))

        xml.append(self.__compile_symbol(")"))
        self.__tokenizer_advance()

        xml.append(self.__compile_symbol("{"))
        self.__tokenizer_advance()

        xml.extend(self.__add_tabs(self.compile_statements()))

        xml.append(self.__compile_symbol("}"))

        xml.append("</whileStatement>")
        return xml

    def compile_do(self) -> Iterable[str]:
        xml = ["<doStatement>"]

        xml.append(self.__compile_keyword({KeywordToken.do_token}))
        self.__tokenizer_advance()

        xml.extend(self.__compile_subroutine_call())
        self.__tokenizer_advance()

        xml.append(self.__compile_symbol(";"))

        xml.append("</doStatement>")
        return xml

    def compile_return(self) -> Iterable[str]:
        xml = ["<returnStatement>"]

        xml.append(self.__compile_keyword({KeywordToken.return_token}))
        self.__tokenizer_advance()

        if self.tokenizer.get_token().value.get_value() != ";":
            xml.extend(self.__add_tabs(self.compile_expression()))

        xml.append(self.__compile_symbol(";"))

        xml.append("</returnStatement>")
        return xml

    def compile_expression(self) -> Iterable[str]:
        xml = ["<expression>"]

        xml.extend(self.__add_tabs(self.compile_term()))

        while self.tokenizer.get_token().value.get_value() in self.binary_operations:
            xml.append(self.__compile_symbol(self.tokenizer.get_token().value.get_value()))
            self.__tokenizer_advance()

            xml.extend(self.__add_tabs(self.compile_term()))

        xml.append("</expression>")
        return xml

    def compile_term(self) -> Iterable[str]:
        xml = ["<term>"]
        token = self.tokenizer.get_token()

        if token.type == TokenType.int_const:
            xml.append(
                f"  <integerConstant> {token.value.get_value()} </integerConstant>"
            )

        if token.type == TokenType.string_const:
            xml.append(
                f"  <stringConstant> {token.value.get_value()} </stringConstant>"
            )

        if token.type == TokenType.keyword and token.value in self.keyword_constants:
            xml.append(self.__compile_keyword(self.keyword_constants))

        if token.value.get_value() == "(":
            xml.append(self.__compile_symbol("("))
            self.__tokenizer_advance()

            xml.extend(self.__add_tabs(self.compile_expression()))

            xml.append(self.__compile_symbol(")"))

        if token.value.get_value() in self.unary_operations:
            xml.append(self.__compile_symbol(token.value.get_value()))
            self.__tokenizer_advance()

            xml.extend(self.__add_tabs(self.compile_term()))
        else:
            self.__tokenizer_advance()

        if token.type == TokenType.identifier:
            next_token = self.tokenizer.get_token()

            if next_token.value.get_value() in "(.":
                xml.extend(self.__compile_subroutine_call(token))
                self.__tokenizer_advance()

            else:
                xml.append(self.__compile_identifier(token))

                if next_token.value.get_value() == "[":
                    xml.append(self.__compile_symbol("["))
                    self.__tokenizer_advance()

                    xml.extend(self.__add_tabs(self.compile_expression()))

                    xml.append(self.__compile_symbol("]"))
                    self.__tokenizer_advance()

        xml.append("</term>")
        return xml

    def compile_expression_list(self) -> Iterable[str]:
        xml = ["<expressionList>"]

        if self.tokenizer.get_token().value.get_value() != ")":
            xml.extend(self.__add_tabs(self.compile_expression()))

            while self.tokenizer.get_token().value.get_value() == ",":
                xml.append(self.__compile_symbol(","))
                self.__tokenizer_advance()

                xml.extend(self.__add_tabs(self.compile_expression()))

        xml.append("</expressionList>")
        return xml

    def __tokenizer_advance(self) -> None:
        assert self.tokenizer.has_next()
        self.tokenizer.advance()

    def __compile_symbol(self, symbol_str: str) -> str:
        symbol = self.tokenizer.get_token()
        assert symbol.type == TokenType.symbol
        assert symbol.value.get_value() == symbol_str
        return f"  <symbol> {XMLSymbols.get_xml_symbol(symbol_str)} </symbol>"

    def __compile_identifier(self, prev_token: Token | None = None) -> str:
        id = prev_token if prev_token else self.tokenizer.get_token()
        assert id.type == TokenType.identifier
        return f"  <identifier> {id.value.get_value()} </identifier>"

    def __compile_keyword(self, keywords: set[KeywordToken]) -> str:
        keyword = self.tokenizer.get_token()
        assert keyword.type == TokenType.keyword
        assert keyword.value in keywords
        return f"  <keyword> {keyword.value.get_value().lower()} </keyword>"

    def __compile_subroutine_call(
        self, prev_token: Token | None = None
    ) -> Iterable[str]:
        xml = []

        xml.append(self.__compile_identifier(prev_token))
        if not prev_token:
            self.tokenizer.advance()

        token = self.tokenizer.get_token()
        if token.value.get_value() == ".":
            xml.append(self.__compile_symbol("."))
            self.__tokenizer_advance()

            xml.append(self.__compile_identifier())
            self.__tokenizer_advance()

        xml.append(self.__compile_symbol("("))
        self.__tokenizer_advance()

        xml.extend(self.__add_tabs(self.compile_expression_list()))

        xml.append(self.__compile_symbol(")"))

        return xml

    def __add_tabs(self, xml: Iterable[str]) -> Iterable[str]:
        indented_xml = []

        for line in xml:
            indented_xml.append(f"  {line}")

        return indented_xml
