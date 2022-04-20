from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Iterable


class Command:
    @staticmethod
    def get_command(line: str) -> Command:
        line = line.lstrip()

        if len(line) == 0 or line[0] == "/":
            return EmptyCommand()

        if line[0] == "@":
            return ACommand()
        if line[0] == "(":
            return LCommand()

        return CCommand()

    @abstractmethod
    def parse(self, line: str, symbol_table: SymbolTable) -> str | None:
        pass


class ACommand(Command):
    def parse(self, line: str, symbol_table: SymbolTable) -> str | None:
        line = line.lstrip()

        line = line[1:]
        address_string = line.partition(" ")[0]  # Get the address rigth after @
        address = 0

        if address_string.isnumeric():
            address = int(address_string)
        else:
            address = symbol_table[address_string]

        # convert int to binary, remove 0b prefix, add 0's at the start
        instruction: str = bin(address)[2:].rjust(16, "0")
        return instruction


class CCommand(Command):
    def parse(self, line: str, symbol_table: SymbolTable) -> str | None:
        instruction = "111"
        line = line.lstrip()

        # Remove comments
        line = line.partition("//")[0].rstrip()

        dest: str = "000"
        comp: str = "0000000"
        jump: str = "000"

        if "=" in line:
            dest = self.__get_dest(line.partition("=")[0])
            line = line.partition("=")[-1]

        if ";" in line:
            jump = self.__get_jump(line.partition(";")[-1])
            line = line.partition(";")[0]

        comp = self.__get_comp(line)

        instruction = instruction + comp + dest + jump

        return instruction

    def __get_dest(self, assembly_command: str) -> str:
        instruction = "000"

        if "M" in assembly_command:
            instruction = instruction[:-1] + "1"

        if "D" in assembly_command:
            instruction = instruction[0] + "1" + instruction[2]

        if "A" in assembly_command:
            instruction = "1" + instruction[1:]

        return instruction

    def __get_comp(self, assembly_command: str) -> str:
        a = "1" if "M" in assembly_command else "0"
        register = "M" if "M" in assembly_command else "A"

        comp_insruction_map: dict[str, str] = {
            "0": "101010",
            "1": "111111",
            "-1": "111010",
            "D": "001100",
            f"{register}": "110000",
            "!D": "001101",
            f"!{register}": "110001",
            "-D": "001111",
            f"-{register}": "110011",
            "D+1": "011111",
            f"{register}+1": "110111",
            "D-1": "001110",
            f"{register}-1": "110010",
            f"D+{register}": "000010",
            f"D-{register}": "010011",
            f"{register}-D": "000111",
            f"D&{register}": "000000",
            f"D|{register}": "010101",
        }

        return a + comp_insruction_map[assembly_command]

    def __get_jump(self, assembly_command: str) -> str:
        command_map: dict[str, str] = {
            "JGT": "001",
            "JEQ": "010",
            "JGE": "011",
            "JLT": "100",
            "JNE": "101",
            "JLE": "110",
            "JMP": "111",
        }

        return command_map[assembly_command]


class LCommand(Command):
    def parse(self, line: str, symbol_table: SymbolTable) -> str | None:
        return None


class EmptyCommand(Command):
    def parse(self, line: str, symbol_table: SymbolTable) -> str | None:
        return None


class SymbolTable(dict[str, int]):
    def __init__(self, assembly: Iterable[str]) -> None:
        self.__ram_address = 16

        self.__add_predifined()
        self.__get_labels(assembly)

    def __getitem__(self, key: str) -> int:
        if key not in self:
            self[key] = self.__ram_address
            self.__ram_address += 1

        return super().__getitem__(key)

    def __add_predifined(self) -> None:
        self["SP"] = 0
        self["LCL"] = 1
        self["ARG"] = 2
        self["THIS"] = 3
        self["THAT"] = 4
        self["SCREEN"] = 16384
        self["KBD"] = 24576

        for i in range(0, 16):
            self[f"R{i}"] = i

    def __get_labels(self, assembly: Iterable[str]) -> None:
        program_counter = 0

        for line in assembly:
            line = line.lstrip()

            if type(Command.get_command(line)) == EmptyCommand:
                continue

            if type(Command.get_command(line)) == LCommand:
                self[line[1:-1]] = program_counter
                continue

            program_counter += 1


@dataclass
class Assembler:
    @classmethod
    def create(cls) -> Assembler:
        return cls()

    def assemble(self, assembly: Iterable[str]) -> Iterable[str]:
        hack: list[str] = []
        self.symbol_table: SymbolTable = SymbolTable(assembly)

        for line in assembly:
            instruction: str | None = Command.get_command(line).parse(
                line, self.symbol_table
            )

            if instruction:
                hack.append(instruction)

        return hack
