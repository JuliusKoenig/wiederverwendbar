from pathlib import Path
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, Text

from sqlalchemy.orm import relationship

from wiederverwendbar.logger import LoggerSingleton, LoggerSettings, LogLevels
from wiederverwendbar.sqlalchemy import Base, SqlalchemySettings, SqlalchemyDbSingleton

LoggerSingleton(name="test", settings=LoggerSettings(log_level=LogLevels.DEBUG), init=True)
SqlalchemyDbSingleton(settings=SqlalchemySettings(db_file=Path("test.db")), init=True)


class MyBase(Base, SqlalchemyDbSingleton().Base):
    __abstract__ = True


class Parent(MyBase):
    __tablename__ = "parent"
    __str_columns__: list[str] = ["id", "name"]

    id: int = Column(Integer(), primary_key=True, autoincrement=True, name="parent_id")
    name: str = Column(Text(50), nullable=False, unique=True)
    children: list["Child"] = relationship("Child",
                                           foreign_keys="Child.parent_id",
                                           primaryjoin="Parent.id == Child.parent_id",
                                           viewonly=True)


class Child(MyBase):
    __tablename__ = "child"
    __str_columns__: list[str] = ["id", "name"]

    id: int = Column(Integer(), primary_key=True, autoincrement=True, name="parent_id")
    name: str = Column(Text(50), nullable=False, unique=True)
    parent_id: int = Column(Integer(), ForeignKey("parent.parent_id"), nullable=False, name="child_parent_id")
    parent: Optional[Parent] = relationship("Parent",
                                            foreign_keys="Parent.id",
                                            primaryjoin="Child.parent_id == Parent.id")


if __name__ == '__main__':
    SqlalchemyDbSingleton().create_all()

    parent1 = Parent.get(name="parent1")
    if parent1 is None:
        parent1 = Parent(name="parent1")
        parent1.save()

    child1 = Child.get(name="child1")
    if child1 is None:
        child1 = Child(name="child1", parent_id=parent1.id)
        child1.save()

    child2 = Child.get(name="child2")
    if child2 is None:
        child2 = Child(name="child2", parent_id=parent1.id)
        child2.save()

    child3 = Child.get(name="child3")
    if child3 is None:
        child3 = Child(name="child3", parent_id=parent1.id)
        child3.save()

    parent2 = Parent.get(name="parent2")
    if parent2 is None:
        parent2 = Parent(name="parent2")
        parent2.save()

    child4 = Child.get(name="child4")
    if child4 is None:
        child4 = Child(name="child4", parent_id=parent2.id)
        child4.save()

    child5 = Child.get(name="child5")
    if child5 is None:
        child5 = Child(name="child5", parent_id=parent2.id)
        child5.save()

    child6 = Child.get(name="child6")
    if child6 is None:
        child6 = Child(name="child6", parent_id=parent2.id)
        child6.save()

    Parent.delete_all()  # Should raise an IntegrityError --> FOREIGN KEY constraint failed
    parent2.delete() # Should raise an IntegrityError --> FOREIGN KEY constraint failed

    print()
