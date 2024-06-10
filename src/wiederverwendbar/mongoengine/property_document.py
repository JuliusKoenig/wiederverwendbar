from typing import Any, Union

from mongoengine import Document


class PropertyDocument(Document):
    meta = {"abstract": True}

    def __getitem__(self, item: Union[int, str]) -> Any:
        """
        Get item from model

        :param item: Index or key
        :return: Index value or key value
        """

        # check if is a property
        if hasattr(self, item):
            attr = getattr(self.__class__, item)
            if isinstance(attr, property):
                return getattr(self, item)

        return super().__getitem__(item)

