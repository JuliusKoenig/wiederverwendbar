import inspect

from mongoengine.base import BaseDocument, BaseField


class WithInstanceField(BaseField):
    def get_instance(self) -> BaseDocument:
        """
        Get the instance of the document that the field is attached to.
        :return: The instance of the document that the field is attached to.
        """

        # get stack
        stack = inspect.stack()

        # get the instance of the document that the field is attached to
        for frame in stack:
            if "self" in frame.frame.f_locals:
                if not isinstance(frame.frame.f_locals["self"], self.owner_document):
                    continue
                return frame.frame.f_locals["self"]
        raise ValueError("Could not find instance of document that the field is attached to.")
