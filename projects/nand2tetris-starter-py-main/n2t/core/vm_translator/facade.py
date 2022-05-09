from __future__ import annotations

from abc import abstractmethod
from typing import Iterable


class VmTranslator:
    @classmethod
    def create(cls) -> VmTranslator:
        return cls()

    def translate(self, vm_code: Iterable[str]) -> Iterable[str]:
        asm: list[str] = []

        for line in vm_code:
            asm.extend(Command.get_command(line).parse(line))

        return asm


class Command:
    @staticmethod
    def get_command(line: str) -> Command:
        line = line.lstrip()

        if len(line) == 0 or line[0:2] == "//":
            return EmptyCommand()

        if line[0:4] == "push":
            return PushCommand()

        if line[0:3] == "pop":
            return PopCommand()

        return ArithmeticCommand()

    @abstractmethod
    def parse(self, line: str) -> Iterable[str]:
        line = line.strip()
        return [f"// {line}"]


class EmptyCommand(Command):
    def parse(self, line: str) -> Iterable[str]:
        if line[0:2] == "//":
            line = line[2:]
        return super().parse(line)


class PushCommand(Command):
    def parse(self, line: str) -> Iterable[str]:
        line = line.strip()
        line_tokenized = line.split()
        assert line_tokenized[0] == "push"

        asm = list(super().parse(line))

        if line_tokenized[1] == "constant":
            asm.extend(self.__constant(line_tokenized[2]))

        return asm

    def __constant(self, value: str) -> list[str]:
        asm = []
        asm.append(f"@{value}")  # D = value
        asm.append("D=A")
        asm.append("@SP")  # *SP = D
        asm.append("A=M")
        asm.append("M=D")
        asm.append("@SP")  # SP++
        asm.append("M=M+1")
        return asm

    def __storage(self) -> list[str]:
        """
        This method generates assembly code for local, argument,
        this and that segments
        """
        pass

    def __compiler_helper(self) -> list[str]:
        """
        This method generates assembly code for pointer and temp
        segments
        """
        pass

    def __static(self) -> list[str]:
        pass


class PopCommand(Command):
    def parse(self, line: str) -> Iterable[str]:
        pass


class ArithmeticCommand(Command):
    __operations: dict[str, str] = {
        "add": "+",
        "sub": "-",
        "neg": "-",
        "eq": "JEQ",
        "gt": "JGT",
        "lt": "JLT",
        "and": "&",
        "or": "|",
        "not": "!",
    }
    __label_count = 0

    def parse(self, line: str) -> Iterable[str]:
        line = line.strip()
        assert line in self.__operations

        asm = list(super().parse(line))
        operation = self.__operations[line]

        if line == "not" or line == "neg":
            asm.extend(self.__one_var_operation(operation))

        elif line == "eq" or line == "gt" or line == "lt":
            asm.extend(self.__compare_operation(operation))

        else:
            asm.extend(self.__two_var_operation(operation))

        return asm

    def __two_var_operation(self, operation: str) -> list[str]:
        asm = []
        asm.append("@SP")  # SP-- // get stack to its final place i.e. pop first var
        asm.append("M=M-1")
        asm.append("A=M")  # D = *SP // save first var
        asm.append("D=M")
        asm.append("A=A-1")  # *(SP - 1) = ? // do operation between vars
        asm.append(f"M=M{operation}D")
        return asm

    def __one_var_operation(self, operation: str) -> list[str]:
        asm = []
        asm.append("@SP")  # *(SP - 1) = ? // modify variable acording to need
        asm.append("A=M-1")
        asm.append(f"M={operation}M")
        return asm

    def __compare_operation(self, operation: str) -> list[str]:
        asm = self.__two_var_operation(self.__operations["sub"])

        asm.append("D=M")  # save current value
        asm.append(f"@SET_TRUE_{ArithmeticCommand.__label_count}")
        asm.append(f"D;{operation}")  # if operation: set_true
        asm.append("@SP")  # else set false (*(SP-1)=0)
        asm.append("A=M-1")
        asm.append("M=0")
        asm.append(f"@END_COMPARE_{ArithmeticCommand.__label_count}")
        asm.append("0;JMP")
        asm.append(f"(SET_TRUE_{ArithmeticCommand.__label_count})")  # *(SP-1)=-1
        asm.append("@SP")
        asm.append("A=M-1")
        asm.append("M=-1")
        asm.append(f"(END_COMPARE_{ArithmeticCommand.__label_count})")

        ArithmeticCommand.__label_count += 1
        return asm
