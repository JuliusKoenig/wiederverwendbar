import json
import sys
from warnings import warn
from pathlib import Path
from typing import Any, Union, Literal

from pydantic import BaseModel, create_model

from wiederverwendbar.warnings import FileNotFoundWarning


class FileConfig(BaseModel):
    def __init__(self,
                 file_path: Union[Path, str, None] = None,
                 file_postfix: str = ".json",
                 file_must_exist: Union[bool, Literal["yes_print", "yes_warn", "yes_raise", "no"]] = "no",
                 **overwrite_data: Any):
        if file_path is None:
            file_path = Path(Path.cwd() / self.__class__.__name__.lower()).with_suffix(file_postfix)
        else:
            file_path = Path(file_path)
            if file_path.suffix == "":
                file_path = file_path.with_suffix(file_postfix)
        file_path = file_path.absolute()

        # read data from file
        if file_path.is_file():
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        elif file_path.is_dir():
            raise ValueError(f"{self.__class__.__name__} file path '{file_path}' is a directory.")
        else:
            if file_must_exist is True:
                file_must_exist = "yes_raise"
            elif file_must_exist is False:
                file_must_exist = "no"
            msg = f"{self.__class__.__name__} file '{file_path}' not found."
            if file_must_exist == "yes_print":
                print(msg)
                sys.exit(1)
            elif file_must_exist == "yes_warn":
                warn(msg, FileNotFoundWarning)
                sys.exit(1)
            elif file_must_exist == "yes_raise":
                raise FileNotFoundError(msg)
            data = {}

        # overwrite data
        for k, v in overwrite_data.items():
            data[k] = v

        super().__init__(**data)

        self._file_path = file_path

    @property
    def file_path(self) -> Path:
        """
        File path

        :return: Path
        """

        return self._file_path

    def save(self, validate: bool = True, indent: int = 4, encoding: str = "utf-8"):
        if validate:
            validate_model_info = {}
            for field_name, field_info in self.model_fields.items():
                validate_model_info[field_name] = (field_info.annotation, field_info)
            validate_model = create_model(f"{self.__class__.__name__}_Validate", **validate_model_info)

            params = self.model_dump()
            validated = validate_model(**params)
            self_json = validated.model_dump_json(indent=indent)
        else:
            self_json = self.model_dump_json(indent=indent)

        with self.file_path.open("w", encoding=encoding) as file:
            file.write(self_json)
