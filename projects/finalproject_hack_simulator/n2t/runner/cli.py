from typer import Option, Typer, echo

from n2t.infra.hack_simulator import HackSimProgram

cli = Typer(
    name="NAND 2 Tetris Hack Simulator",
    no_args_is_help=True,
    add_completion=False,
)


@cli.command("execute", no_args_is_help=True)
def run_simulator(
    hack_file: str, cycles: int = Option(10000, help="Number of CPU cycles")
) -> None:
    echo(f"Disassembling {hack_file}")
    HackSimProgram.load_from(hack_file, cycles).simulate()
    echo("Done!")
