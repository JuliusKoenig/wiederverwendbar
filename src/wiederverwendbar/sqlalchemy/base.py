from typing import Any, Optional, Callable, Union, TYPE_CHECKING

from sqlalchemy import inspect
from sqlalchemy.sql import ColumnExpressionArgument
from sqlalchemy.orm import Session, QueryableAttribute, InstrumentedAttribute
from sqlalchemy.orm.exc import DetachedInstanceError

from wiederverwendbar.default import Default
from wiederverwendbar.sqlalchemy.raise_has_not_attr import raise_has_not_attr

if TYPE_CHECKING:
    from wiederverwendbar.sqlalchemy.db import SqlalchemyDb


class SelectionError(Exception):
    """Failed to select column value."""


class SerializationError(Exception):
    """Failed to serialize column value."""


class DeserializationError(Exception):
    """Failed to serialize column value."""


class MappingError(Exception):
    """Failed to map column value."""


class DictColumn:
    def __init__(self,
                 key: str,
                 is_primary_key: Union[bool, Default] = Default(),
                 selector: Union[Callable[..., Any], None, Default] = Default(),
                 serializer: Union[Callable[[...], Any], None, Default] = Default(),
                 deserializer: Union[Callable[[...], Any], None, Default] = Default(),
                 mapper: Union[Callable[..., Any], None, Default] = Default()) -> None:
        """
        DictColumn
        Used to select and serialize attributes from the ORM.

        :param key: Key in serial_obj.
        :param is_primary_key: Indicate if column is primary key.
        :param selector: Python code to select value from ORM.
        :param serializer: Python code to serialize value after selecting from ORM.
        :param deserializer: Python code to deserialize value for mapping.
        :param mapper: Python code to map value to ORM after deserializing.
        """

        # key
        self.key = key

        # is_primary_key
        if type(is_primary_key) is Default:
            is_primary_key = False
        self.is_primary_key = is_primary_key

        # selector
        if type(selector) is Default:
            selector = lambda **kw: getattr(kw["base"], kw["key"])
        self.selector = selector

        # serializer
        if type(serializer) is Default:
            serializer = None
        self.serializer = serializer

        # deserializer
        if type(deserializer) is Default:
            deserializer = None
        self.deserializer = deserializer

        # mapper
        if type(mapper) is Default:
            mapper = lambda **kw: raise_has_not_attr(kw["base"], kw["key"]) and setattr(kw["base"], kw["key"], kw["value"])
        self.mapper = mapper

    def __str__(self):
        s = f"{self.__class__.__name__}(key={self.key}"
        s += f", selector={self.selector is not None}"
        s += f", serializer={self.serializer is not None}"
        s += f", deserializer={self.deserializer is not None}"
        s += f", mapper={self.mapper is not None}"
        s += ")"
        return s

    def __eq__(self, other) -> bool:
        if type(other) is not DictColumn:
            return self.key == other
        else:
            return self.key == other.key and self.selector == other.selector and self.serializer == other.serializer

    def select(self, base: "Base") -> Any:
        if not isinstance(base, Base):
            raise AttributeError(f"Attribute 'base' must be a instance of Base, not {type(base)}")
        if self.selector is None:
            value = ...
        else:
            try:
                value = self.selector(key=self.key, base=base)
            except Exception as e:
                raise SelectionError(e) from e
        return value

    def serialize(self, value: Any) -> dict[str, Any]:
        # serialize
        try:
            if self.serializer is not None:
                value = self.serializer(value)
        except Exception as e:
            raise SerializationError(e) from e
        return value

    def deserialize(self, value: Any) -> Any:
        # deserialize
        try:
            if self.deserializer is not None:
                value = self.deserializer(value)
        except Exception as e:
            raise DeserializationError(e) from e
        return value

    def map(self, value: Any, base: "Base") -> None:
        if not isinstance(base, Base):
            raise AttributeError(f"Attribute 'base' must be a instance of Base, not {type(base)}")
        if self.mapper is not None:
            try:
                self.mapper(key=self.key, value=value, base=base)
            except Exception as e:
                raise SelectionError(e) from e


class Base:
    __abstract__ = True
    __allow_unmapped__ = True
    __str_columns__: list[str] = []
    db: "SqlalchemyDb"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"{self.__class__.__name__}({', '.join([f'{column_name}={getattr(self, column_name)}' for column_name in self.__str_columns__])})"

    def __repr__(self):
        return self.__str__()

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except DetachedInstanceError:
            with self.db.session() as session:
                my_id = getattr(self, "id", None)
                if my_id is None:
                    raise Exception(f"{self.__class__.__name__} has no id!")
                obj = session.query(self.__class__).filter_by(id=my_id).first()
                if obj is None:
                    raise Exception(f"{self.__class__.__name__} with id {my_id} not found!")
                return getattr(obj, item)

    @classmethod
    def _default_dict_columns(cls) -> list[DictColumn]:
        # get inspection obj
        cls_inspect = inspect(cls)

        # create dict columns
        dict_columns = []
        for column_attrs in cls_inspect.mapper.column_attrs:
            dict_column = DictColumn(key=column_attrs.key, is_primary_key=column_attrs.expression.primary_key)
            dict_columns.append(dict_column)

        return dict_columns

    def as_dict(self, dict_columns: Union[list[DictColumn], Default] = Default()) -> dict[str, Any]:
        # create DictColumns if not given
        if type(dict_columns) is Default:
            dict_columns = self._default_dict_columns()

        # progress
        serial_obj = {}
        for dict_column in dict_columns:
            # check if key already in serial_obj
            if dict_column.key in serial_obj:
                raise SerializationError(f"Key '{self.key}' is already exist in serial_obj!")

            # select from base
            value = dict_column.select(base=self)
            if value is ...:
                continue

            # serialize to serial_obj
            serial_obj[dict_column.key] = dict_column.serialize(value=value)
        return serial_obj

    @classmethod
    def from_dict(cls, serial_obj: dict[str, Any], dict_columns: Union[list[DictColumn], Default] = Default()) -> "Base":
        # create DictColumns if not given
        if type(dict_columns) is Default:
            dict_columns = cls._default_dict_columns()

        # built get kwargs
        get_kwargs = {}
        for dict_column in dict_columns:
            if not dict_column.is_primary_key:
                continue

            # select from serial_obj
            value = serial_obj[dict_column.key]

            # deserialize
            get_kwargs[dict_column.key] = dict_column.deserialize(value=value)

        # get base
        if get_kwargs:
            base = cls.get(**get_kwargs)
        else:
            base = cls()

        # progress
        for dict_column in dict_columns:
            # select from serial_obj
            value = serial_obj[dict_column.key]

            # deserialize
            value = dict_column.deserialize(value=value)

            # map
            dict_column.map(value=value, base=base)
        return base

    @classmethod
    def session(cls, session: Union[Session] = None) -> tuple[bool, Session]:
        # create new session
        session_created = False
        if session is None:
            session = cls.db.session()
            session_created = True
        return session_created, session

    @classmethod
    def session_close(cls, session_created: bool, session: Session) -> None:
        # close session
        if session_created:
            session.close()

    @classmethod
    def new(cls,
            session: Optional[Session] = None,
            **kwargs) -> "Base":
        session_created, session = cls.session(session=session)

        # noinspection PyArgumentList
        obj: Base = cls(**kwargs)
        session.add(obj)
        session.commit()
        session.refresh(obj)

        cls.session_close(session_created=session_created, session=session)

        return obj

    @classmethod
    def length(cls,
               *criterion: Union[ColumnExpressionArgument[bool], bool],
               session: Optional[Session] = None,
               **kwargs: Any) -> int:
        session_created, session = cls.session(session=session)

        if criterion:
            length = session.query(cls).filter(*criterion, **kwargs).count()
        else:
            length = session.query(cls).filter_by(**kwargs).count()

        cls.session_close(session_created=session_created, session=session)

        return length

    @classmethod
    def get_all(cls,
                *criterion: Union[ColumnExpressionArgument[bool], bool],
                order_by: Union[str, QueryableAttribute, None] = None,
                order_desc: bool = False,
                rows_per_page: Optional[int] = None,
                page: int = 1,
                fill_empty: bool = False,
                as_dict: bool = False,
                dict_columns: Union[list[DictColumn], Default] = Default(),
                session: Optional[Session] = None,
                **kwargs: Any) -> list[Union["Base", None, dict[str, Any]]]:
        session_created, session = cls.session(session=session)

        # get order by
        if order_by is not None:
            if type(order_by) is str:
                order_by = getattr(cls, order_by)
            if not isinstance(order_by, QueryableAttribute):
                raise AttributeError(f"Attribute 'order_by' must be a instance of QueryableAttribute, not {type(order_by)}")
            if order_desc:
                order_by = order_by.desc()

        if rows_per_page is not None:
            # get length
            length = cls.length(*criterion, **kwargs)
            lst = []
            if length == 0:
                return lst
            offset = (page - 1) * rows_per_page

            # add empty rows before partial select
            if fill_empty:
                # noinspection PyTypeChecker
                for i in range(offset):
                    if as_dict:
                        lst.append({})
                    else:
                        lst.append(None)

            # get rows
            if criterion:
                lst_partial: list[Any] = session.query(cls).filter(*criterion, **kwargs).order_by(order_by).limit(rows_per_page).offset(offset).all()
            else:
                lst_partial: list[Any] = session.query(cls).filter_by(**kwargs).order_by(order_by).limit(rows_per_page).offset(offset).all()

            for row in lst_partial:
                lst.append(row.as_dict(dict_columns=dict_columns) if as_dict else row)

            # add empty rows after partial select
            if fill_empty:
                # noinspection PyTypeChecker
                for i in range(offset + rows_per_page, length):
                    if as_dict:
                        lst.append({})
                    else:
                        lst.append(None)
        else:
            if criterion:
                lst: list[Any] = session.query(cls).order_by(order_by).filter(*criterion, **kwargs).all()
            else:
                lst: list[Any] = session.query(cls).order_by(order_by).filter_by(**kwargs).all()
            if as_dict:
                lst = [row.as_dict(dict_columns=dict_columns) for row in lst]

        cls.session_close(session_created=session_created, session=session)

        return lst

    @classmethod
    def get(cls,
            *criterion: Union[ColumnExpressionArgument[bool], bool],
            as_dict: bool = False,
            dict_columns: Union[list[DictColumn], Default] = Default(),
            session: Optional[Session] = None,
            **kwargs: Any) -> Union["Base", None, dict[str, Any]]:
        session_created, session = cls.session(session=session)

        if criterion:
            obj: Any = session.query(cls).filter(*criterion, **kwargs).first()
        else:
            obj: Any = session.query(cls).filter_by(**kwargs).first()

        if as_dict:
            if obj is None:
                obj = {}
            else:
                obj = obj.as_dict(dict_columns=dict_columns)

        cls.session_close(session_created=session_created, session=session)

        return obj

    def save(self, session: Optional[Session] = None) -> "Base":
        session_created, session = self.session(session=session)

        session.add(self)
        session.commit()
        session.refresh(self)

        self.session_close(session_created=session_created, session=session)

        return self

    def update(self, session: Optional[Session] = None, **kwargs) -> "Base":
        session_created, session = self.session(session=session)

        for column, value in kwargs.items():
            setattr(self, column, value)

        self.save()

        self.session_close(session_created=session_created, session=session)

        return self

    def delete(self, session: Optional[Session] = None) -> None:
        session_created, session = self.session(session=session)

        session.delete(self)
        session.commit()

        self.session_close(session_created=session_created, session=session)
