from pydantic import BaseModel, Field, computed_field
from wiederverwendbar.pydantic.file import BaseFile
from wiederverwendbar.pydantic.file.json import JsonFile


class SampleFile(BaseFile):
    class Sub(BaseModel):
        sub_attr_str: str = Field(default=..., title="Sub Attribute 1", description="This is a sub attribute 1")
        sub_attr_int: int = Field(default=..., title="Sub Attribute 2", description="This is a sub attribute 2")
        sub_attr_float: float = Field(default=..., title="Sub Attribute 3", description="This is a sub attribute 3")
        sub_attr_bool: bool = Field(default=..., title="Sub Attribute 4", description="This is a sub attribute 4")

    attr_str1: str = Field(default=..., title="Test String 1", description="This is a test string attribute 1")
    attr_str2: str = Field(default=..., title="Test String 2", description="This is a test string attribute 2")
    attr_int1: int = Field(default=..., title="Test Integer 1", description="This is a test integer attribute 1")
    attr_int2: int = Field(default=..., title="Test Integer 2", description="This is a test integer attribute 2")
    attr_float1: float = Field(default=..., title="Test Float 1", description="This is a test float attribute 1")
    attr_float2: float = Field(default=..., title="Test Float 2", description="This is a test float attribute 2")
    attr_bool1: bool = Field(default=..., title="Test Boolean 1", description="This is a test boolean attribute 1")
    attr_bool2: bool = Field(default=..., title="Test Boolean 2", description="This is a test boolean attribute 2")
    attr_sub: Sub = Field(default=..., title="Test Sub Model", description="This is a test sub model attribute")
    attr_list_sub: list[Sub] = Field(
        default_factory=list,
        title="Test List of Sub Models",
        description="This is a test list of sub model attributes"
    )

    @computed_field
    @property
    def attr_computed(self) -> str:
        return f"{self.attr_str1} {self.attr_str2}"

class SampleFileJson(SampleFile, JsonFile):
    class Config:
        file_name = "custom"
        file_must_exist = "no_print"
        file_save_on_load = "if_not_exist"
        file_json_encode_indent = 4


if __name__ == "__main__":
    overwrite={
        "attr_str1": "Hello",
        "attr_str2": "World",
        "attr_int1": 42,
        "attr_int2": 7,
        "attr_float1": 3.14,
        "attr_float2": 2.71,
        "attr_bool1": True,
        "attr_bool2": False,
        "attr_sub": {
            "sub_attr_str": "asd",
            "sub_attr_int": 123,
            "sub_attr_float": 1.23,
            "sub_attr_bool": True
        },
        "attr_list_sub": [
            {
                "sub_attr_str": "qwe",
                "sub_attr_int": 456,
                "sub_attr_float": 4.56,
                "sub_attr_bool": False
            },
            {
                "sub_attr_str": "zxc",
                "sub_attr_int": 789,
                "sub_attr_float": 7.89,
                "sub_attr_bool": True
            }
        ]
    }

    sample = SampleFileJson.load(file_overwrite=overwrite)

    # sample.reload()

    sample.save()
