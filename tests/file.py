import os
import string
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel, Field
from pydantic._internal._model_construction import ModelMetaclass

DEFAULT_FILE_PATH = Path(os.getcwd())


class FileConfigBase:
    abstract: bool = False
    filename: Optional[str] = None
    file_path: Union[None, str, Path] = None


class FileModelMetaclass(ModelMetaclass):
    def __new__(mcs, name: str, bases: tuple[type[Any], ...], namespace: dict[str, Any], **kwargs: Any) -> type:
        # get config
        config: type[FileConfigBase] | type = namespace.get("Config", type("Config", (), {}))

        # set config attributes if not present
        for key, value in FileConfigBase.__dict__.items():
            if key.startswith("_"):
                continue
            if hasattr(config, key):
                continue
            setattr(config, key, value)

        # if not abstract, set dynamic attributes to config
        if not config.abstract:
            # filename
            if config.filename is None:
                word_split = []
                word = ""
                for char in name:
                    if char in string.ascii_uppercase + string.digits + string.punctuation + string.whitespace:
                        if word:
                            word_split.append(word)
                            word = ""
                    word += char.lower()
                if word:
                    word_split.append(word)
                config.filename = "_".join(word_split)

            # file_path
            if config.file_path is None:
                config.file_path = DEFAULT_FILE_PATH
            elif isinstance(config.file_path, str):
                config.file_path = Path(config.file_path)

        return ModelMetaclass.__new__(mcs, name, bases, namespace, **kwargs)


class FileModel(BaseModel, metaclass=FileModelMetaclass):
    ...

    class Config:
        abstract = True


class SampleFile(FileModel):
    class Config:
        file_config = "qwe"

    attr_str1: str = Field(default=..., title="Test String 1", description="This is a test string attribute 1")
    attr_str2: str = Field(default=..., title="Test String 2", description="This is a test string attribute 2")
    attr_int1: int = Field(default=..., title="Test Integer 1", description="This is a test integer attribute 1")
    attr_int2: int = Field(default=..., title="Test Integer 2", description="This is a test integer attribute 2")
    attr_float1: float = Field(default=..., title="Test Float 1", description="This is a test float attribute 1")
    attr_float2: float = Field(default=..., title="Test Float 2", description="This is a test float attribute 2")
    attr_bool1: bool = Field(default=..., title="Test Boolean 1", description="This is a test boolean attribute 1")
    attr_bool2: bool = Field(default=..., title="Test Boolean 2", description="This is a test boolean attribute 2")


if __name__ == "__main__":
    sample = SampleFile(
        attr_str1="Hello",
        attr_str2="World",
        attr_int1=42,
        attr_int2=7,
        attr_float1=3.14,
        attr_float2=2.71,
        attr_bool1=True,
        attr_bool2=False
    )
    print()
