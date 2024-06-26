from ipaddress import IPv4Network

from mongoengine.base.fields import BaseField


class IPv4NetworkField(BaseField):
    def validate(self, value, clean=True):
        super().validate(value, clean)
        try:
            IPv4Network(value)
        except ValueError:
            self.error(f"Invalid IPv4 network: {value}")

    def to_mongo(self, value):
        return str(value)

    def to_python(self, value):
        return IPv4Network(value)
