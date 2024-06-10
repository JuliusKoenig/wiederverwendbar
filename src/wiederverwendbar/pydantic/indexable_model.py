from typing import Any, Union

from pydantic import BaseModel


class IndexableModel(BaseModel):
    def __getitem__(self, item: Union[int, str]) -> Any:
        """
        Get item from model

        :param item: Index or key
        :return: Index value or key value
        """

        if isinstance(item, int):
            # get field list
            fields = list(self.model_fields.keys())

            # get field name
            field_name = fields[item]

            # get field value
            value = self.__getattribute__(field_name)
        elif isinstance(item, str):
            # get field value
            value = self.__getattribute__(item)
        else:
            raise TypeError(f"Index must be int or str not {type(item)}")

        return value