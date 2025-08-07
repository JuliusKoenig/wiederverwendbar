from pydantic import Field

from wiederverwendbar.pydantic.file_config import JsonFileConfig


class Config(JsonFileConfig):
    asd: int = Field(123, le=150)
    qwe: str = "qwe"
    yxc: bool = False


if __name__ == '__main__':
    c = Config.load()
    c.asd = 120
    c.save(exclude=["qwe"])
    print()
