from ipaddress import IPv4Address

from mongoengine.base.fields import BaseField


class IPv4AddressField(BaseField):
    def validate(self, value, clean=True):
        super().validate(value, clean)
        try:
            IPv4Address(value)
        except ValueError:
            self.error(f"Invalid IPv4 address: {value}")

    def to_mongo(self, value):
        return str(value)

    def to_python(self, value):
        return IPv4Address(value)
