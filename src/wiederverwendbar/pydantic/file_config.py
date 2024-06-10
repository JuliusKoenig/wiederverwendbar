import json
from pathlib import Path
from typing import Any, Union

from pydantic import BaseModel, create_model


class FileConfig(BaseModel):
    def __init__(self,
                 file_path: Union[Path, str, None] = None,
                 file_postfix: str = ".json",
                 file_must_exist: bool = False,
                 **overwrite_data: Any):
        if file_path is None:
            file_path = Path(Path.cwd() / self.__class__.__name__.lower()).with_suffix(file_postfix)
        else:
            file_path = Path(file_path)
            if file_path.suffix == "":
                file_path = file_path.with_suffix(file_postfix)

        # read data from file
        if file_path.is_file():
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        elif file_path.is_dir():
            raise ValueError(f"{self.__class__.__name__} file path '{file_path}' is a directory.")
        else:
            if file_must_exist:
                raise FileNotFoundError(f"{self.__class__.__name__} file '{file_path}' not found.")
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
