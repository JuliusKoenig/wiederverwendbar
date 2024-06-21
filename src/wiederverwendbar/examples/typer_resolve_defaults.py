import typer
from wiederverwendbar.typer import typer_resolve_defaults

app = typer.Typer()


@app.command()
@typer_resolve_defaults
def main(a: str, name: str = typer.Argument(default="World1"), qwe: str = typer.Option(default_factory=lambda: "qwe")):
    print(f"Hello {name}")


if __name__ == "__main__":
    main(a="a1")
    app()
