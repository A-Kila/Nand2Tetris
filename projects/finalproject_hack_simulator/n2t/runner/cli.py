from typer import Option, Typer

cli = Typer(
    name="NAND 2 Tetris Hack Simulator",
    no_args_is_help=True,
    add_completion=False,
)


@cli.command("execute", no_args_is_help=True)
def run_simulator(
    hack_file: str, cycles: int = Option(10000, help="Number of CPU cycles")
) -> None:
    pass
