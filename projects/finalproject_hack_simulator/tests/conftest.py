from pathlib import Path
from typing import Iterable

import pytest


@pytest.fixture(scope="module")
def hack_directory(pytestconfig: pytest.Config) -> Iterable[Path]:
    name = pytestconfig.rootpath.joinpath("tests", "hack")

    yield name


@pytest.fixture(scope="module")
def cmp_directory(pytestconfig: pytest.Config) -> Iterable[Path]:
    name = pytestconfig.rootpath.joinpath("tests", "cmp")

    yield name
