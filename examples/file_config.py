from wiederverwendbar.pydantic.file_config import FileConfig


class Config(FileConfig):
    asd: int = 123
    qwe: str = "qwe"
    yxc: bool = False


if __name__ == '__main__':
    config = Config(file_path="test")
