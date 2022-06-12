from enum import Enum


class Segment(Enum):
    const = "constant"
    arg = "argument"
    local = "local"
    static = "static"
    this = "this"
    that = "that"
    pointer = "pointer"
    temp = "temp"


class VmCommand(Enum):
    add = "add"
    subtract = "sub"
    negation = "neg"
    equal = "eq"
    greater_than = "gt"
    less_than = "lt"
    log_and = "and"
    log_or = "or"
    log_not = "not"
    multiply = "call Math.multiply 2"
    divide = "call Math.divide 2"


class VmWritter:
    def write_push(self, segment: Segment, index: int) -> str:
        return f"push {segment.value} {index}"

    def write_pop(self, segment: Segment, index: int) -> str:
        return f"pop {segment.value} {index}"

    def write_arthmetic(self, command: VmCommand) -> str:
        return command.value

    def write_label(self, label: str) -> str:
        return f"label {label}"

    def write_goto(self, label: str) -> str:
        return f"goto {label}"

    def write_if(self, label: str) -> str:
        return f"if-goto {label}"

    def write_call(self, name: str, num_args: int) -> str:
        return f"call {name} {num_args}"

    def write_function(self, name: str, num_locals: int) -> str:
        return f"function {name} {num_locals}"

    def write_return(self) -> str:
        return "return"
