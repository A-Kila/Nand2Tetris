import filecmp
from pathlib import Path

import pytest

from n2t.runner.cli import run_simulator

_TEST_PROGRAMS = [
    "Add",
    "Jump",
    "SimpleAdd",
    "StackTest",
    "StaticTest",
]


@pytest.mark.parametrize("program", _TEST_PROGRAMS)
def test_should_simulate(
    program: str, hack_directory: Path, cmp_directory: Path
) -> None:
    asm_file = str(hack_directory.joinpath(f"{program}.hack"))

    run_simulator(asm_file)

    assert filecmp.cmp(
        shallow=False,
        f1=str(cmp_directory.joinpath(f"{program}.cmp")),
        f2=str(hack_directory.joinpath(f"{program}.out")),
    )
