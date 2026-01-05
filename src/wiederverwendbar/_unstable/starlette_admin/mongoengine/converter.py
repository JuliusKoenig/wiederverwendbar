from wiederverwendbar.starlette_admin.mongoengine.boolean_also_field.converter import BooleanAlsoConverter
from wiederverwendbar.starlette_admin.mongoengine.generic_embedded_document_field.converter import GenericEmbeddedConverter
from wiederverwendbar.starlette_admin.mongoengine.ipv4_field.converter import IPv4Converter


class MongoengineConverter(GenericEmbeddedConverter, IPv4Converter, BooleanAlsoConverter):
    ...
