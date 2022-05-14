from __future__ import annotations

from abc import abstractmethod
from typing import Iterable


class VmTranslator:
    @classmethod
    def create(cls) -> VmTranslator:
        return cls()

    def translate(self, file_name: str, vm_code: Iterable[str]) -> Iterable[str]:
        asm: list[str] = []

        for line in vm_code:
            asm.extend(Command.get_command(file_name, line).parse(line))

        return asm


class Command:
    @staticmethod
    def get_command(
        file_name: str, line: str, function_name: str | None = None
    ) -> Command:
        line = line.lstrip()

        if len(line) == 0 or line[0:2] == "//":
            return EmptyCommand(file_name)

        if line[0:4] == "push":
            return PushCommand(file_name)

        if line[0:3] == "pop":
            return PopCommand(file_name)

        if line[0:5] == "label":
            return LabelCommand(file_name, function_name)

        if line[0:4] == "goto":
            return GotoCommand(file_name, function_name)

        if line[0:7] == "if-goto":
            return IfGotoCommand(file_name, function_name)

        return ArithmeticCommand(file_name)

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name

    @abstractmethod
    def parse(self, line: str) -> Iterable[str]:
        line = line.strip()
        return [f"// {line}"]


class EmptyCommand(Command):
    def parse(self, line: str) -> Iterable[str]:
        if line[0:2] == "//":
            line = line[2:]
        return super().parse(line)


class SegmentCommand(Command):
    __segment_asm_names = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT",
        "temp": "R5",
    }

    @property
    @abstractmethod
    def command_string(self) -> str:
        pass

    @property
    def segment_asm_names(self) -> dict[str, str]:
        return self.__segment_asm_names

    def parse(self, line: str) -> Iterable[str]:
        line = line.strip()
        line_tokenized = line.split()

        assert line_tokenized[0] == self.command_string
        segment = line_tokenized[1]
        value = line_tokenized[2]

        asm = list(super().parse(line))

        if segment == "constant":
            asm.extend(self.constant(value))

        elif segment == "pointer" or segment == "static":
            asm.extend(self.pointer(value, segment == "static"))

        else:
            asm.extend(self.storage(segment, value))

        return asm

    @abstractmethod
    def constant(self, value: str) -> list[str]:
        pass

    @abstractmethod
    def storage(self, segment: str, value: str) -> list[str]:
        """
        This method generates assembly code for local, argument,
        this, that and temp segments
        """
        pass

    @abstractmethod
    def pointer(self, value: str, is_static: bool) -> list[str]:
        pass


class PushCommand(SegmentCommand):
    @property
    def command_string(self) -> str:
        return "push"

    def constant(self, value: str) -> list[str]:
        asm = []
        asm.append(f"@{value}")  # D = value
        asm.append("D=A")
        asm.append("@SP")  # *SP = D
        asm.append("A=M")
        asm.append("M=D")
        asm.append("@SP")  # SP++
        asm.append("M=M+1")
        return asm

    def storage(self, segment: str, value: str) -> list[str]:
        asm_segment = self.segment_asm_names[segment]
        segment_pointer_storage = "A" if segment == "temp" else "M"

        asm = []
        asm.append(f"@{value}")  # D = value
        asm.append("D=A")
        asm.append(f"@{asm_segment}")  # addr = segment_pointer + D
        asm.append(f"A={segment_pointer_storage}+D")
        asm.append("D=M")  # D = *addr
        asm.append("@SP")  # *SP = D
        asm.append("A=M")
        asm.append("M=D")
        asm.append("@SP")  # SP++
        asm.append("M=M+1")
        return asm

    def pointer(self, value: str, is_static: bool) -> list[str]:
        if is_static:
            address = f"{self.file_name}.{value}"
        else:
            address = "THIS" if value == "0" else "THAT"

        asm = []
        asm.append(f"@{address}")  # D = THIS/THAT
        asm.append("D=M")
        asm.append("@SP")  # *SP = D
        asm.append("A=M")
        asm.append("M=D")
        asm.append("@SP")  # SP++
        asm.append("M=M+1")
        return asm


class PopCommand(SegmentCommand):
    @property
    def command_string(self) -> str:
        return "pop"

    def constant(self, value: str) -> list[str]:
        assert False

    def storage(self, segment: str, value: str) -> list[str]:
        asm_segment = self.segment_asm_names[segment]
        segment_pointer_storage = "A" if segment == "temp" else "M"

        asm = []
        asm.append(f"@{value}")  # D = value
        asm.append("D=A")
        asm.append(f"@{asm_segment}")  # D = addr = segmentPoint + D
        asm.append(f"D={segment_pointer_storage}+D")
        asm.append("@R13")  # R13 = D
        asm.append("M=D")
        asm.append("@SP")  # SP--
        asm.append("M=M-1")
        asm.append("A=M")  # D = *SP
        asm.append("D=M")
        asm.append("@R13")  # *addr = D
        asm.append("A=M")
        asm.append("M=D")
        return asm

    def pointer(self, value: str, is_static: bool) -> list[str]:
        if is_static:
            address = f"{self.file_name}.{value}"
        else:
            address = "THIS" if value == "0" else "THAT"

        asm = []
        asm.append("@SP")  # SP--
        asm.append("M=M-1")
        asm.append("A=M")  # D = *SP
        asm.append("D=M")
        asm.append(f"@{address}")  # THIS/THAT = D
        asm.append("M=D")
        return asm


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


class LabelCommand(Command):
    def __init__(self, file_name: str, function_name: str | None) -> None:
        super().__init__(file_name)
        self.function_name = function_name

    def parse(self, line: str) -> Iterable[str]:
        asm = list(super().parse(line))

        vm_label = line.split()[1]
        asm_label = LabelCommand.get_asm_label(
            vm_label, self.file_name, self.function_name
        )

        asm.append(f"({asm_label})")
        return asm

    @staticmethod
    def get_asm_label(label: str, file_name: str, function_name: str | None) -> str:
        return (
            f"{file_name}."
            + (function_name + "$" if function_name else "")
            + f"{label}"
        )


class GotoCommand(Command):
    def __init__(self, file_name: str, function_name: str | None) -> None:
        super().__init__(file_name)
        self.function_name = function_name

    def parse(self, line: str) -> Iterable[str]:
        asm = list(super().parse(line))

        vm_label = line.split()[1]
        asm_label = LabelCommand.get_asm_label(
            vm_label, self.file_name, self.function_name
        )

        asm.append(f"@{asm_label}")  # jump to LABEL
        asm.append("0; JMP")

        return asm


class IfGotoCommand(Command):
    def __init__(self, file_name: str, function_name: str | None) -> None:
        super().__init__(file_name)
        self.function_name = function_name

    def parse(self, line: str) -> Iterable[str]:
        asm = list(super().parse(line))

        vm_label = line.split()[1]
        asm_label = LabelCommand.get_asm_label(
            vm_label, self.file_name, self.function_name
        )

        asm.append("@SP")  # D = *(--SP)
        asm.append("AM=M-1")
        asm.append("D=M")
        asm.append(f"@{asm_label}")  # if D + 1 == 0:  goto Label
        asm.append("D;JNE")

        return asm


class Fucntion(Command):
    pass
