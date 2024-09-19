from mongoengine import IntField


class PortField(IntField):
    def __init__(self, **kwargs):
        super().__init__(min_value=1, max_value=65535, **kwargs)
