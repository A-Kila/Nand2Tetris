from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Registers:
    PC: int = 0
    D: int = 0
    A: int = 0


@dataclass
class Ram:
    size: int = 2**15
    values: dict[int, int] = field(default_factory=lambda: {})

    def get_size(self) -> int:
        return self.size

    def set(self, address: int, value: int) -> None:
        assert address < self.size

        self.values[address] = value

    def get(self, address: int) -> tuple[bool, int]:
        assert address < self.size

        return (address in self.values, self.values.get(address, 0))


class Instruction(Protocol):
    def proccess(self, binary_instruction: str, registers: Registers, ram: Ram) -> None:
        pass


class AInstuction:
    def proccess(self, binary_instruction: str, registers: Registers, _: Ram) -> None:
        registers.A = int(binary_instruction, 2)


@dataclass
class CInstruction:
    def proccess(self, binary_instruction: str, registers: Registers, ram: Ram) -> None:
        comp = self.__get_comp(binary_instruction, registers, ram)
        self.__set_dest(binary_instruction, registers, ram, comp)
        self.__jump(binary_instruction, registers, comp)

    def __get_comp(
        self, binary_instruction: str, registers: Registers, ram: Ram
    ) -> int:
        register = (
            registers.A if binary_instruction[3] == "0" else ram.get(registers.A)[1]
        )

        comp_insruction_map: dict[str, int] = {
            "101010": 0,
            "111111": 1,
            "111010": -1,
            "001100": registers.D,
            "110000": register,
            "001101": self.__not(registers.D),
            "110001": self.__not(register),
            "001111": -registers.D,
            "110011": -register,
            "011111": registers.D + 1,
            "110111": register + 1,
            "001110": registers.D - 1,
            "110010": register - 1,
            "000010": registers.D + register,
            "010011": registers.D - register,
            "000111": register - registers.D,
            "000000": registers.D & register,
            "010101": registers.D | register,
        }

        return comp_insruction_map[binary_instruction[4:10]]

    def __set_dest(
        self, binary_instruction: str, registers: Registers, ram: Ram, comp: int
    ) -> None:
        if binary_instruction[10] == "1":
            registers.A = comp

        if binary_instruction[11] == "1":
            registers.D = comp

        if binary_instruction[12] == "1":
            ram.set(registers.A, comp)

    def __jump(self, binary_instruction: str, registers: Registers, comp: int) -> None:
        if (
            (binary_instruction[13] == "1" and comp < 0)
            or (binary_instruction[14] == "1" and comp == 0)
            or (binary_instruction[15] == "1" and comp > 0)
        ):
            registers.PC = registers.A - 1

    def __not(self, value: int) -> int:
        return -value - 1


class HackParser:
    def parse(self, binary_instruction: str) -> Instruction:
        if binary_instruction[0] == "0":
            return AInstuction()

        return CInstruction()


@dataclass
class HackSimulator:
    registers: Registers = field(default_factory=Registers)
    ram: Ram = field(default_factory=Ram)
    hack_parser: HackParser = field(default_factory=HackParser)

    @classmethod
    def create(cls) -> HackSimulator:
        return cls()

    def simulate(self, hack: list[str], cycles: int) -> Ram:
        for _ in range(cycles):
            if self.registers.PC >= len(hack):
                break

            binary_instruction = hack[self.registers.PC]
            machine_instruction = self.hack_parser.parse(binary_instruction)
            machine_instruction.proccess(binary_instruction, self.registers, self.ram)

            self.registers.PC += 1

        return self.ram
