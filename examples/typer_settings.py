from wiederverwendbar.typer import TyperSettings, TyperApp

settings = TyperSettings(cli_name="test_app",
                         cli_help="Test App")
app = TyperApp(settings=settings)


@app.command()
def test1():
    app.console.print("test1")


@app.command()
def test2():
    app.console.print("test2")


if __name__ == "__main__":
    app()
