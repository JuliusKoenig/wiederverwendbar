from wiederverwendbar import __author__, __author_email__, __license__, __license_url__, __terms_of_service__
from wiederverwendbar.typer import TyperSettings, Typer, SubTyper

settings = TyperSettings(branding_title="Test App",
                         branding_description="Test Description",
                         branding_version="0.1.0",
                         branding_author=__author__,
                         branding_author_email=__author_email__,
                         branding_license=__license__,
                         branding_license_url=__license_url__,
                         branding_terms_of_service=__terms_of_service__)
app = Typer(settings=settings)


@app.command()
def test1():
    app.console.print("test1")


@app.command()
def test2():
    app.console.print("test2")


sub_app = SubTyper()

@sub_app.command()
def sub_test1():
    sub_app.console.print("sub_test1")

sub_sub_app = SubTyper()

@sub_sub_app.command()
def sub_sub_test1():
    sub_sub_app.console.print("sub_test1")

sub_app.add_typer(sub_sub_app, name="sub-sub")

app.add_typer(sub_app, name="sub")


if __name__ == "__main__":
    app()
