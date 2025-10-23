from typing import TYPE_CHECKING

from typer import Typer as _Typer

from wiederverwendbar.rich.console import RichConsole

if TYPE_CHECKING:
    from wiederverwendbar.typer.app import Typer


class SubTyper(_Typer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._parent: "Typer | SubTyper | None" = None


    @property
    def parent(self) -> "Typer | SubTyper":
        if self._parent is None:
            raise ValueError("This SubTyper instance does not have a parent assigned.")
        return self._parent

    @property
    def root(self) -> "Typer":
        if hasattr(self.parent, "root"):
            return self.parent.root
        return self.parent

    @property
    def console(self) -> RichConsole:
        return self.root.console

    def add_typer(self, typer_instance: _Typer, **kwargs) -> None:
        super().add_typer(typer_instance, **kwargs)
        if isinstance(typer_instance, SubTyper):
            if typer_instance._parent is not None:
                if typer_instance._parent is not self:
                    raise ValueError("The SubTyper instance already has a parent assigned.")
            typer_instance._parent = self

