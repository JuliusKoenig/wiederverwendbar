from typing import Any

import starlette_admin as sa
from starlette_admin.contrib.mongoengine.converters import ModelConverter, converts

from wiederverwendbar.mongoengine.fields.ipv4_address_field import IPv4AddressField
from wiederverwendbar.mongoengine.fields.ipv4_network_field import IPv4NetworkField


class IPv4Converter(ModelConverter):
    @converts(IPv4AddressField, IPv4NetworkField)
    def conv_ipv4_field(self, *args: Any, **kwargs: Any) -> sa.BaseField:
        return sa.StringField(**self._field_common(*args, **kwargs))
