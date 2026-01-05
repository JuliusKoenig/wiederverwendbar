from wiederverwendbar.typer import SubTyper

sub_app = SubTyper()


@sub_app.command()
def sub_test1():
    sub_app.console.print("sub_test1")


sub_sub_app = SubTyper()


@sub_sub_app.command()
def sub_sub_test1():
    sub_sub_app.console.print("sub_test1")


sub_app.add_typer(sub_sub_app, name="sub-sub")
