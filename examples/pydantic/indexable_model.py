from wiederverwendbar.pydantic.indexable_model import IndexableModel


class Config(IndexableModel):
    asd: int = 123
    qwe: str = "qwe"
    yxc: bool = False


if __name__ == '__main__':
    config = Config()

    asd = config["asd"]
    qwe = config["qwe"]
    yxc = config["yxc"]

    asd_1 = config[0]
    qwe_1 = config[1]
    yxc_1 = config[2]
