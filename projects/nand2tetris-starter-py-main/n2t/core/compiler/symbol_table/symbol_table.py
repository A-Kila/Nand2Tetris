from dataclasses import dataclass
from enum import Enum


class Scope(Enum):
    field = "field"
    static = "static"
    argument = "argument"
    local = "local"


@dataclass
class Symbol:
    name: str
    type: str
    scope: Scope
    is_used: bool
    index: int


class SymbolTable(dict[str, Symbol]):
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.indexes: dict[Scope, int] = {
            Scope.field: 0,
            Scope.static: 0,
            Scope.argument: 0,
            Scope.local: 0,
        }

        self.clear()

    def define(self, name: str, type: str, scope: Scope) -> None:
        index = self.indexes[scope]
        self.indexes[scope] += 1

        self[name] = Symbol(name, type, scope, False, index)

    def var_count(self, scope: Scope) -> int:
        return len(list(filter(lambda var: scope == var.scope, self.values())))
