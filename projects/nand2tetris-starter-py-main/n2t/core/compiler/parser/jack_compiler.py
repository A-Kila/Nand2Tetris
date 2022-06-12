from dataclasses import dataclass, field
from typing import Iterable

from n2t.core.compiler.symbol_table.symbol_table import Scope, Symbol, SymbolTable
from n2t.core.compiler.tokenizer.token import KeywordToken, Token, TokenType
from n2t.core.compiler.tokenizer.tokenizer_facade import JackTokenizer
from n2t.core.compiler.vm_writer.vm_writer import Segment, VmCommand, VmWritter


class Label:
    index = 0

    @classmethod
    def get_label(cls) -> str:
        label = f"LABEL_{cls.index}"
        cls.index += 1
        return label


@dataclass
class JackCompiler:
    tokenizer: JackTokenizer
    __vm_writer: VmWritter = VmWritter()

    __class_name: str = ""
    __locals_table: SymbolTable = field(default_factory=SymbolTable)
    __globals_table: SymbolTable = field(default_factory=SymbolTable)

    __binary_operations = {
        "+": VmCommand.add,
        "-": VmCommand.subtract,
        "*": VmCommand.multiply,
        "/": VmCommand.divide,
        "&": VmCommand.log_and,
        "|": VmCommand.log_or,
        "<": VmCommand.less_than,
        ">": VmCommand.greater_than,
        "=": VmCommand.equal,
    }
    __unary_operations = {"-": VmCommand.negation, "~": VmCommand.log_not}

    __keyword_constants = {
        KeywordToken.true_token,
        KeywordToken.false_token,
        KeywordToken.null_token,
        KeywordToken.this_token,
    }

    def compile_class(self) -> Iterable[str]:
        vm = ["// class"]

        self.__assert_keyword({KeywordToken.class_token})
        self.__tokenizer_advance()

        self.__assert_identifier()
        self.__class_name = self.tokenizer.get_token().value.get_value()
        self.__tokenizer_advance()

        self.__assert_symbol("{")
        self.__tokenizer_advance()

        while self.tokenizer.get_token().type == TokenType.keyword and (
            self.tokenizer.get_token().value == KeywordToken.static_token
            or self.tokenizer.get_token().value == KeywordToken.field_token
        ):
            vm.extend(self.compile_class_var_dec())
            self.__tokenizer_advance()

        while self.tokenizer.get_token().type == TokenType.keyword and (
            self.tokenizer.get_token().value == KeywordToken.constructor_token
            or self.tokenizer.get_token().value == KeywordToken.function_token
            or self.tokenizer.get_token().value == KeywordToken.method_token
        ):
            vm.extend(self.compile_subroutine_dec())
            self.__tokenizer_advance()

        self.__assert_symbol("}")
        assert not self.tokenizer.has_next()

        return vm

    def compile_class_var_dec(self) -> Iterable[str]:
        vm = ["// class var dec"]

        self.__assert_keyword({KeywordToken.static_token, KeywordToken.field_token})
        scope = Scope(self.tokenizer.get_token().value.get_value())
        self.__tokenizer_advance()

        vm.extend(self.compile_type())
        type = self.tokenizer.get_token().value.get_value()
        self.__tokenizer_advance()

        self.__assert_identifier()
        name = self.tokenizer.get_token().value.get_value()
        self.__tokenizer_advance()

        self.__globals_table.define(name, type, scope)

        while (
            self.tokenizer.get_token().type == TokenType.symbol
            and self.tokenizer.get_token().value.get_value() == ","
        ):
            self.__assert_symbol(",")
            self.tokenizer.advance()

            self.__assert_identifier()
            name = self.tokenizer.get_token().value.get_value()
            self.tokenizer.advance()

            self.__globals_table.define(name, type, scope)

        self.__assert_symbol(";")

        return vm

    def compile_type(self) -> Iterable[str]:
        type_token = self.tokenizer.get_token()
        assert (
            type_token.type == TokenType.keyword
            or type_token.type == TokenType.identifier
        )

        if type_token.type == TokenType.keyword:
            self.__assert_keyword(
                {
                    KeywordToken.int_token,
                    KeywordToken.char_token,
                    KeywordToken.bool_token,
                }
            )

        else:
            self.__assert_identifier()

        return []

    def compile_subroutine_dec(self) -> Iterable[str]:
        vm = ["// subroutine dec"]

        self.__assert_keyword(
            {
                KeywordToken.constructor_token,
                KeywordToken.function_token,
                KeywordToken.method_token,
            }
        )
        keyword = self.tokenizer.get_token().value
        self.__locals_table.reset()
        self.__tokenizer_advance()

        return_type = self.tokenizer.get_token()
        if return_type.value == KeywordToken.void_token:
            self.__assert_keyword({KeywordToken.void_token})
            self.__tokenizer_advance()

        else:
            vm.extend(self.compile_type())
            self.__tokenizer_advance()

        self.__assert_identifier()
        subroutine_name = self.tokenizer.get_token().value.get_value()
        vm_func_name = f"{self.__class_name}.{subroutine_name}"
        self.__tokenizer_advance()

        self.__assert_symbol("(")
        self.__tokenizer_advance()

        # token advance happend inside function
        vm.extend(self.compile_parameter_list(keyword))

        self.__assert_symbol(")")
        self.__tokenizer_advance()

        vm.extend(self.compile_subroutine_body(vm_func_name, keyword))

        return vm

    def compile_parameter_list(self, keyword: KeywordToken) -> Iterable[str]:
        vm = ["// parameter list"]

        if keyword == KeywordToken.method_token:
            self.__locals_table.define("this", self.__class_name, Scope.argument)

        token = self.tokenizer.get_token()
        if token.type == TokenType.keyword or token.type == TokenType.identifier:
            vm.extend(self.compile_type())
            type = self.tokenizer.get_token().value.get_value()
            self.__tokenizer_advance()

            self.__assert_identifier()
            name = self.tokenizer.get_token().value.get_value()
            self.__tokenizer_advance()

            self.__locals_table.define(name, type, Scope.argument)

            while self.tokenizer.get_token().value.get_value() == ",":
                self.__assert_symbol(",")
                self.__tokenizer_advance()

                vm.extend(self.compile_type())
                type = self.tokenizer.get_token().value.get_value()
                self.__tokenizer_advance()

                self.__assert_identifier()
                name = self.tokenizer.get_token().value.get_value()
                self.__tokenizer_advance()

                self.__locals_table.define(name, type, Scope.argument)

        return vm

    def compile_subroutine_body(
        self, func_name: str, keyword: KeywordToken
    ) -> Iterable[str]:
        vm = ["// subroutine body"]

        self.__assert_symbol("{")
        self.__tokenizer_advance()

        while self.tokenizer.get_token().value == KeywordToken.var_token:
            vm.extend(self.compile_var_dec())
            self.__tokenizer_advance()

        num_locals = self.__locals_table.var_count(Scope.local)
        vm.append(self.__vm_writer.write_function(func_name, num_locals))

        if keyword == KeywordToken.constructor_token:
            num_fields = self.__globals_table.var_count(Scope.field)
            vm.append(self.__vm_writer.write_push(Segment.const, num_fields))
            vm.append(self.__vm_writer.write_call("Memory.alloc", 1))
            vm.append(self.__vm_writer.write_pop(Segment.pointer, 0))

        elif keyword == KeywordToken.method_token:
            vm.append(self.__vm_writer.write_push(Segment.arg, 0))
            vm.append(self.__vm_writer.write_pop(Segment.pointer, 0))

        vm.extend(self.compile_statements())

        self.__assert_symbol("}")

        return vm

    def compile_var_dec(self) -> Iterable[str]:
        vm = ["// var dec"]

        self.__assert_keyword({KeywordToken.var_token})
        self.__tokenizer_advance()

        vm.extend(self.compile_type())
        type = self.tokenizer.get_token().value.get_value()
        self.__tokenizer_advance()

        self.__assert_identifier()
        name = self.tokenizer.get_token().value.get_value()
        self.__tokenizer_advance()

        self.__locals_table.define(name, type, Scope.local)

        while self.tokenizer.get_token().value.get_value() == ",":
            self.__assert_symbol(",")
            self.__tokenizer_advance()

            self.__assert_identifier()
            name = self.tokenizer.get_token().value.get_value()
            self.__tokenizer_advance()

            self.__locals_table.define(name, type, Scope.local)

        self.__assert_symbol(";")

        return vm

    def compile_statements(self) -> Iterable[str]:
        vm = ["// statements"]

        while self.tokenizer.get_token().value in {
            KeywordToken.let_token,
            KeywordToken.if_token,
            KeywordToken.while_token,
            KeywordToken.do_token,
            KeywordToken.return_token,
        }:
            value = self.tokenizer.get_token().value

            if value == KeywordToken.let_token:
                vm.extend(self.compile_let())
                self.__tokenizer_advance()

            if value == KeywordToken.if_token:
                vm.extend(self.compile_if())

            if value == KeywordToken.while_token:
                vm.extend(self.compile_while())
                self.__tokenizer_advance()

            if value == KeywordToken.do_token:
                vm.extend(self.compile_do())
                self.__tokenizer_advance()

            if value == KeywordToken.return_token:
                vm.extend(self.compile_return())
                self.__tokenizer_advance()

        return vm

    def compile_let(self) -> Iterable[str]:
        vm = ["// let statement"]

        self.__assert_keyword({KeywordToken.let_token})
        self.__tokenizer_advance()

        self.__assert_identifier()
        variable = self.__get_variable(self.tokenizer.get_token().value.get_value())
        segment = Segment(
            variable.scope.value if variable.scope != Scope.field else "this"
        )
        self.__tokenizer_advance()

        is_array = False
        if self.tokenizer.get_token().value.get_value() == "[":
            is_array = True
            self.__assert_symbol("[")
            self.__tokenizer_advance()

            vm.append(self.__vm_writer.write_push(segment, variable.index))

            vm.extend(self.compile_expression())
            vm.append(self.__vm_writer.write_arthmetic(VmCommand.add))

            self.__assert_symbol("]")
            self.__tokenizer_advance()

        self.__assert_symbol("=")
        self.__tokenizer_advance()

        vm.extend(self.compile_expression())

        self.__assert_symbol(";")

        if is_array:
            vm.append(self.__vm_writer.write_pop(Segment.temp, 0))
            vm.append(self.__vm_writer.write_pop(Segment.pointer, 1))
            vm.append(self.__vm_writer.write_push(Segment.temp, 0))
            vm.append(self.__vm_writer.write_pop(Segment.that, 0))

        else:
            vm.append(self.__vm_writer.write_pop(segment, variable.index))

        return vm

    def compile_if(self) -> Iterable[str]:
        vm = ["// if statement"]

        label_else = Label.get_label()
        label_end = Label.get_label()

        self.__assert_keyword({KeywordToken.if_token})
        self.__tokenizer_advance()

        self.__assert_symbol("(")
        self.__tokenizer_advance()

        vm.extend(self.compile_expression())
        vm.append(self.__vm_writer.write_arthmetic(VmCommand.log_not))

        self.__assert_symbol(")")
        self.__tokenizer_advance()

        vm.append(self.__vm_writer.write_if(label_else))

        self.__assert_symbol("{")
        self.__tokenizer_advance()

        vm.extend(self.compile_statements())

        self.__assert_symbol("}")
        self.__tokenizer_advance()

        vm.append(self.__vm_writer.write_goto(label_end))
        vm.append(self.__vm_writer.write_label(label_else))

        if self.tokenizer.get_token().value == KeywordToken.else_token:
            self.__assert_keyword({KeywordToken.else_token})
            self.__tokenizer_advance()

            self.__assert_symbol("{")
            self.__tokenizer_advance()

            vm.extend(self.compile_statements())

            self.__assert_symbol("}")
            self.__tokenizer_advance()

        vm.append(self.__vm_writer.write_label(label_end))

        return vm

    def compile_while(self) -> Iterable[str]:
        vm = ["// while statement"]

        loop_start_label = Label.get_label()
        loop_end_label = Label.get_label()

        self.__assert_keyword({KeywordToken.while_token})
        vm.append(self.__vm_writer.write_label(loop_start_label))
        self.__tokenizer_advance()

        self.__assert_symbol("(")
        self.__tokenizer_advance()

        vm.extend(self.compile_expression())

        self.__assert_symbol(")")
        self.__tokenizer_advance()

        vm.append(self.__vm_writer.write_arthmetic(VmCommand.log_not))
        vm.append(self.__vm_writer.write_if(loop_end_label))

        self.__assert_symbol("{")
        self.__tokenizer_advance()

        vm.extend(self.compile_statements())

        self.__assert_symbol("}")

        vm.append(self.__vm_writer.write_goto(loop_start_label))
        vm.append(self.__vm_writer.write_label(loop_end_label))

        return vm

    def compile_do(self) -> Iterable[str]:
        vm = ["// do statement"]

        self.__assert_keyword({KeywordToken.do_token})
        self.__tokenizer_advance()

        vm.extend(self.__compile_subroutine_call())
        self.__tokenizer_advance()

        self.__assert_symbol(";")
        vm.append(self.__vm_writer.write_pop(Segment.temp, 0))

        return vm

    def compile_return(self) -> Iterable[str]:
        vm = ["// return statement"]

        self.__assert_keyword({KeywordToken.return_token})
        self.__tokenizer_advance()

        if self.tokenizer.get_token().value.get_value() != ";":
            vm.extend(self.compile_expression())
        else:
            vm.append(self.__vm_writer.write_push(Segment.const, 0))

        self.__assert_symbol(";")
        vm.append(self.__vm_writer.write_return())

        return vm

    def compile_expression(self) -> Iterable[str]:
        vm = ["// expression"]

        vm.extend(self.compile_term())

        while self.tokenizer.get_token().value.get_value() in self.__binary_operations:
            operation_str = self.tokenizer.get_token().value.get_value()
            operation_command = self.__binary_operations[operation_str]
            self.__tokenizer_advance()

            vm.extend(self.compile_term())
            vm.append(self.__vm_writer.write_arthmetic(operation_command))

        return vm

    def compile_term(self) -> Iterable[str]:
        vm = ["// term"]
        token = self.tokenizer.get_token()

        if token.type == TokenType.int_const:
            int_value = token.value.get_value()
            vm.append(self.__vm_writer.write_push(Segment.const, int_value))

        if token.type == TokenType.string_const:
            string_value = token.value.get_value()
            vm.extend(self.__write_string(string_value))

        if token.type == TokenType.keyword and token.value in self.__keyword_constants:
            vm.extend(self.__write_keyword_const(token.value))

        if token.value.get_value() == "(":
            self.__assert_symbol("(")
            self.__tokenizer_advance()

            vm.extend(self.compile_expression())

            self.__assert_symbol(")")

        if token.value.get_value() in self.__unary_operations:
            operation_string = token.value.get_value()
            self.__assert_symbol(operation_string)
            operation_command = self.__unary_operations[operation_string]
            self.__tokenizer_advance()

            vm.extend(self.compile_term())
            vm.append(self.__vm_writer.write_arthmetic(operation_command))
        else:
            self.__tokenizer_advance()

        if token.type == TokenType.identifier:
            next_token = self.tokenizer.get_token()

            if next_token.value.get_value() in "(.":
                vm.extend(self.__compile_subroutine_call(token))
                self.__tokenizer_advance()

            else:
                self.__assert_identifier(token)
                variable = self.__get_variable(token.value.get_value())
                segment = Segment(
                    variable.scope.value if variable.scope != Scope.field else "this"
                )
                vm.append(self.__vm_writer.write_push(segment, variable.index))

                if next_token.value.get_value() == "[":
                    self.__assert_symbol("[")
                    self.__tokenizer_advance()

                    vm.extend(self.compile_expression())
                    vm.append(self.__vm_writer.write_arthmetic(VmCommand.add))

                    vm.append(self.__vm_writer.write_pop(Segment.pointer, 1))
                    vm.append(self.__vm_writer.write_push(Segment.that, 0))

                    self.__assert_symbol("]")
                    self.__tokenizer_advance()

        return vm

    def compile_expression_list(self) -> tuple[Iterable[str], int]:
        vm = ["// expression list"]
        num_args = 0

        if self.tokenizer.get_token().value.get_value() != ")":
            vm.extend(self.compile_expression())
            num_args += 1

            while self.tokenizer.get_token().value.get_value() == ",":
                self.__assert_symbol(",")
                self.__tokenizer_advance()

                vm.extend(self.compile_expression())
                num_args += 1

        return vm, num_args

    def __compile_subroutine_call(
        self, prev_token: Token | None = None
    ) -> Iterable[str]:
        vm = ["// subroutine call"]
        num_args = 0

        name_token = prev_token if prev_token else self.tokenizer.get_token()
        self.__assert_identifier(name_token)
        name = name_token.value.get_value()
        if not prev_token:
            self.tokenizer.advance()

        token = self.tokenizer.get_token()
        if token.value.get_value() == ".":
            self.__assert_symbol(".")
            self.__tokenizer_advance()

            if name in self.__locals_table or name in self.__globals_table:
                num_args += 1

                variable = self.__get_variable(name)
                segment = Segment(
                    variable.scope.value if variable.scope != Scope.field else "this"
                )

                name = variable.type
                vm.append(self.__vm_writer.write_push(segment, variable.index))

            self.__assert_identifier()
            name += f".{self.tokenizer.get_token().value.get_value()}"
            self.__tokenizer_advance()

        else:
            num_args += 1
            name = f"{self.__class_name}.{name}"
            vm.append(self.__vm_writer.write_push(Segment.pointer, 0))

        self.__assert_symbol("(")
        self.__tokenizer_advance()

        expr_list_vm, jack_num_args = self.compile_expression_list()
        num_args += jack_num_args
        vm.extend(expr_list_vm)

        self.__assert_symbol(")")

        vm.append(self.__vm_writer.write_call(name, num_args))

        return vm

    def __tokenizer_advance(self) -> None:
        assert self.tokenizer.has_next()
        self.tokenizer.advance()

    def __assert_symbol(self, symbol_str: str) -> None:
        symbol = self.tokenizer.get_token()
        assert symbol.type == TokenType.symbol
        assert symbol.value.get_value() == symbol_str

    def __assert_identifier(self, prev_token: Token | None = None) -> None:
        id = prev_token if prev_token else self.tokenizer.get_token()
        assert id.type == TokenType.identifier

    def __assert_keyword(self, keywords: set[KeywordToken]) -> None:
        keyword = self.tokenizer.get_token()
        assert keyword.type == TokenType.keyword
        assert keyword.value in keywords

    def __write_string(self, string_value: str) -> Iterable[str]:
        vm = ["// string"]

        # Allocate memory for stirng with lenght len(string)
        vm.append(self.__vm_writer.write_push(Segment.const, len(string_value)))
        vm.append(self.__vm_writer.write_call("String.new", 1))

        for char in string_value:
            vm.append(self.__vm_writer.write_push(Segment.const, ord(char)))
            vm.append(self.__vm_writer.write_call("String.appendChar", 2))

        return vm

    def __write_keyword_const(self, keyword: KeywordToken) -> Iterable[str]:
        vm = ["// keyword constant"]
        self.__assert_keyword(self.__keyword_constants)

        if keyword == KeywordToken.true_token:
            vm.append(self.__vm_writer.write_push(Segment.const, 1))
            vm.append(self.__vm_writer.write_arthmetic(VmCommand.negation))

        elif keyword == KeywordToken.this_token:
            vm.append(self.__vm_writer.write_push(Segment.pointer, 0))

        else:
            vm.append(self.__vm_writer.write_push(Segment.const, 0))

        return vm

    def __get_variable(self, var_name: str) -> Symbol:
        assert var_name in self.__locals_table or var_name in self.__globals_table

        if var_name in self.__locals_table:
            return self.__locals_table[var_name]

        return self.__globals_table[var_name]
