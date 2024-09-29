from mongoengine import StringField


class DomainField(StringField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, regex=r"^(?:$|(?=.{1,253}$)(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63})$", **kwargs)
