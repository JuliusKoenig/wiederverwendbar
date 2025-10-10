from typing import Any

from dicttoxml import dicttoxml
from xml.dom.minidom import parseString
from xmltodict import parse

from wiederverwendbar.pydantic.file.base import BaseFile


class XmlFile(BaseFile):
    class Config:
        file_suffix = ".xml"
        file_xml_root = True
        file_xml_custom_root = "root"
        file_xml_encode_indent = None

    class _InstanceConfig(BaseFile._InstanceConfig):
        """
        Instance configuration for json file handling.

        Attributes:
            file_xml_root (bool): Whether to include a root element in the XML output.
            file_xml_custom_root (str): Custom name for the root element if file_xml_root is True.
            file_xml_encode_indent (None | int | str): Indentation for pretty-printing the XML output. If None, no pretty-printing is applied. If an integer is provided, it specifies the number of spaces for indentation. If a string is provided, it is used as the indentation string.
        """

        file_xml_root: bool
        file_xml_custom_root: str
        file_xml_encode_indent: None | int | str

    @property
    def config(self) -> _InstanceConfig:
        return super().config

    @classmethod
    def _to_dict_postprocessor(cls, path, key, value) -> tuple | None:
        if key == "@type":
            if value == "str":
                key = "type"
                value = str
            elif value == "int":
                key = "type"
                value = int
            elif value == "float":
                key = "type"
                value = float
            elif value == "bool":
                key = "type"
                value = bool
            elif value == "dict":
                return None
            elif value == "list":
                key = "type"
                value = list
        elif key == "#text" and isinstance(value, str):
            key = "value"
        elif type(value) == dict:
            if "type" in value and "value" in value and len(value) == 2:
                value = value["type"](value["value"])
            elif "type" in value and "item" in value and len(value) == 2:
                value = value["type"](value["item"])
        return key, value

    @classmethod
    def _to_dict(cls, content: str, config: _InstanceConfig) -> dict:
        data = parse(content, postprocessor=cls._to_dict_postprocessor)

        # remove root if configured
        if config.file_xml_root:
            data = data.get(config.file_xml_custom_root, data)

        return data

    def _from_dict(self, data: dict[str, Any], config: _InstanceConfig) -> str:
        content = dicttoxml(data,
                            root=config.file_xml_root,
                            custom_root=config.file_xml_custom_root,
                            return_bytes=False)
        if config.file_xml_encode_indent is not None:
            if type(config.file_xml_encode_indent) is int:
                indent = " " * config.file_xml_encode_indent
            else:
                indent = str(config.file_xml_encode_indent)
            content = parseString(content).toprettyxml(newl="\n",
                                                       indent=indent)

        return content
