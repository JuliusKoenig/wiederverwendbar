from pathlib import Path

from sqlalchemy import Column, Text, Integer

from wiederverwendbar.logger import LoggerSingleton, LoggerSettings
from wiederverwendbar.sqlalchemy import Base, SqlalchemySettings, SqlalchemyDbSingleton

LoggerSingleton(name="test", settings=LoggerSettings(log_level=LoggerSettings.LogLevels.DEBUG), init=True)


class MyBase(Base, SqlalchemyDbSingleton(settings=SqlalchemySettings(db_file=Path("test.db")), init=True).Base):
    __abstract__ = True


class MyTable(MyBase):
    __tablename__ = "my_table"
    __str_columns__: list[str] = ["name"]

    name = Column(Text(50), primary_key=True)
    value = Column(Integer)


if __name__ == '__main__':
    SqlalchemyDbSingleton().create_all()

    my_table = MyTable(name="test", value=1)

    d = my_table.as_dict()
    my_table.save()

    print()
