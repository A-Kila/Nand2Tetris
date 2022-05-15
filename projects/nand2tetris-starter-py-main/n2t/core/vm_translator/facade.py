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

    def bootstrap(self) -> Iterable[str]:
        asm: list[str] = []

        asm.append("// Bootsrap code")
        asm.append("@256")  # SP = 256
        asm.append("D=A")
        asm.append("@SP")
        asm.append("M=D")
        asm.extend(CallCommand("").parse("call Sys.init 0"))

        return asm


class Command:
    function_name: str | None = None

    @staticmethod
    def get_command(file_name: str, line: str) -> Command:
        line = line.strip()
        command = line.split()[0] if len(line) > 0 else ""

        if command == "" or command == "//":
            return EmptyCommand(file_name)

        if command == "push":
            return PushCommand(file_name)

        if command == "pop":
            return PopCommand(file_name)

        if command == "label":
            return LabelCommand(file_name, Command.function_name)

        if command == "goto":
            return GotoCommand(file_name, Command.function_name)

        if command == "if-goto":
            return IfGotoCommand(file_name, Command.function_name)

        if command == "call":
            return CallCommand(file_name)

        if command == "function":
            function_command = FunctionCommand(file_name)
            function_command.parse(line)
            Command.function_name = function_command.get_name()
            return function_command

        if command == "return":
            return ReturnCommand(file_name)

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
        command = line.split()[0]
        assert command in self.__operations

        asm = list(super().parse(line))
        operation = self.__operations[command]

        if command == "not" or command == "neg":
            asm.extend(self.__one_var_operation(operation))

        elif command == "eq" or command == "gt" or command == "lt":
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
            asm.extend(self.storage(segment, value, segment == "temp"))

        return asm

    @abstractmethod
    def constant(self, value: str) -> list[str]:
        pass

    @abstractmethod
    def storage(self, segment: str, value: str, is_pointer_saved: bool) -> list[str]:
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

    def storage(self, segment: str, value: str, is_pointer_saved: bool) -> list[str]:
        asm_segment = self.segment_asm_names[segment]
        segment_pointer_storage = "A" if is_pointer_saved else "M"

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

    def storage(self, segment: str, value: str, is_pointer_saved: bool) -> list[str]:
        asm_segment = self.segment_asm_names[segment]
        segment_pointer_storage = "A" if is_pointer_saved else "M"

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


class LabelCommand(Command):
    def __init__(self, file_name: str, function_name: str | None) -> None:
        super().__init__(file_name)
        self.function_name = function_name

    def parse(self, line: str) -> Iterable[str]:
        asm = list(super().parse(line))

        vm_label = line.split()[1]
        asm_label = LabelCommand.get_asm_label(vm_label, self.function_name)

        asm.append(f"({asm_label})")
        return asm

    @staticmethod
    def get_asm_label(label: str, function_name: str | None) -> str:
        return (function_name + "$" if function_name else "") + f"{label}"


class GotoCommand(Command):
    def __init__(self, file_name: str, function_name: str | None) -> None:
        super().__init__(file_name)
        self.function_name = function_name

    def parse(self, line: str) -> Iterable[str]:
        asm = list(super().parse(line))

        vm_label = line.split()[1]
        asm_label = LabelCommand.get_asm_label(vm_label, self.function_name)

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
        asm_label = LabelCommand.get_asm_label(vm_label, self.function_name)

        asm.append("@SP")  # D = *(--SP)
        asm.append("AM=M-1")
        asm.append("D=M")
        asm.append(f"@{asm_label}")  # if D + 1 == 0:  goto Label
        asm.append("D;JNE")

        return asm


class CallCommand(Command):
    return_count: int = 0

    def parse(self, line: str) -> Iterable[str]:
        asm = list(super().parse(line))
        function_name = line.split()[1]
        num_args = line.split()[2]

        return_label = f"RETURN_LABEL_{CallCommand.return_count}"

        # Save caller info
        asm.extend(PushCommand(self.file_name).parse(f"push constant {return_label}"))
        asm.extend(PushCommand(self.file_name).storage("local", "0", True))
        asm.extend(PushCommand(self.file_name).storage("argument", "0", True))
        asm.extend(PushCommand(self.file_name).storage("this", "0", True))
        asm.extend(PushCommand(self.file_name).storage("that", "0", True))

        # Update stored pointers
        asm.append("@SP")  # D = SP - 5 - num_args
        asm.append("D=M")  # D = SP
        asm.append("@5")  # D -= 5
        asm.append("D=D-A")
        asm.append(f"@{num_args}")  # D -= num_args
        asm.append("D=D-A")
        asm.append("@ARG")  # ARG = D
        asm.append("M=D")
        asm.append("@SP")  # D = SP
        asm.append("D=M")
        asm.append("@LCL")  # LCL = D
        asm.append("M=D")

        # Jump to function
        asm.append(f"@{FunctionCommand.get_asm_name(function_name)}")
        asm.append("0;JMP")

        asm.append(f"({return_label})")  # define return destination

        CallCommand.return_count += 1
        return asm


class FunctionCommand(Command):
    def parse(self, line: str) -> Iterable[str]:
        asm = list(super().parse(line))
        self.function_name = line.split()[1]
        num_locals = int(line.split()[2])

        asm.append(f"({self.function_name})")

        for _ in range(num_locals):
            asm.extend(PushCommand(self.file_name).parse("push constant 0"))

        return asm

    def get_name(self) -> str:
        assert self.function_name is not None
        return FunctionCommand.get_asm_name(self.function_name)

    @staticmethod
    def get_asm_name(vm_func_name: str) -> str:
        return vm_func_name


class ReturnCommand(Command):
    def parse(self, line: str) -> Iterable[str]:
        asm = list(super().parse(line))

        asm.append("@LCL")  # R14 = end_frame = LCL
        asm.append("D=M")
        asm.append("@R14")
        asm.append("M=D")
        asm.append("@5")  # R15 = return_address = *(R14 - 5)  // D = LCL
        asm.append("A=D-A")
        asm.append("D=M")
        asm.append("@R15")
        asm.append("M=D")

        # return value
        asm.extend(PopCommand(self.file_name).storage("argument", "0", False))
        asm.append("@ARG")  # SP = ARG + 1
        asm.append("D=M")
        asm.append("@SP")
        asm.append("M=D+1")

        asm.extend(self.__restore_pointer("THAT", 1))
        asm.extend(self.__restore_pointer("THIS", 2))
        asm.extend(self.__restore_pointer("ARG", 3))
        asm.extend(self.__restore_pointer("LCL", 4))

        asm.append("@R15")  # goto return_address
        asm.append("A=M")
        asm.append("0;JMP")

        return asm

    def __restore_pointer(self, pointer: str, offset_from_local: int) -> list[str]:
        asm = []

        asm.append("@R14")  # D = *(endframe - position)
        asm.append("D=M")
        asm.append(f"@{offset_from_local}")
        asm.append("A=D-A")
        asm.append("D=M")
        asm.append(f"@{pointer}")  # pointer = D
        asm.append("M=D")

        return asm
