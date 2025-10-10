from typing import Any
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from wiederverwendbar.pydantic.file.base import BaseFile


class YamlFile(BaseFile):
    class Config:
        file_suffix = ".yaml"
        file_yaml_encode_loader = Loader
        file_yaml_encode_dumper = Dumper
        file_yaml_encode_default_style = None
        file_yaml_encode_default_flow_style = False
        file_yaml_encode_canonical = None
        file_yaml_encode_indent = None
        file_yaml_encode_width = None
        file_yaml_encode_allow_unicode = None
        file_yaml_encode_line_break = None
        file_yaml_encode_encoding = None
        file_yaml_encode_explicit_start = None
        file_yaml_encode_explicit_end = None
        file_yaml_encode_version = None
        file_yaml_encode_tags = None
        file_yaml_encode_sort_keys = True

    class _InstanceConfig(BaseFile._InstanceConfig):
        """
        Instance configuration for json file handling.

        Attributes:
            file_yaml_encode_loader (type[Loader] | Any): The YAML loader class to use for decoding.
            file_yaml_encode_dumper (type[Dumper] | Any): The YAML dumper class to use for encoding.
            file_yaml_encode_default_style (str | None): The default style for YAML encoding. If None, the default style is used.
            file_yaml_encode_default_flow_style (bool | None): Whether to use the default flow style for YAML encoding. If None, the default behavior is used.
            file_yaml_encode_canonical (bool | None): Whether to use canonical form for YAML encoding. If None, the default behavior is used.
            file_yaml_encode_indent (int | None): The indentation level for YAML encoding. If None, no indentation is applied.
            file_yaml_encode_width (int | None): The maximum line width for YAML encoding. If None, no line width limit is applied.
            file_yaml_encode_allow_unicode (bool | None): Whether to allow Unicode characters in YAML encoding. If None, the default behavior is used.
            file_yaml_encode_line_break (str | None): The line break style for YAML encoding. If None, the default behavior is used.
            file_yaml_encode_explicit_start (bool | None): Whether to include an explicit start marker in YAML encoding. If None, the default behavior is used.
            file_yaml_encode_explicit_end (bool | None): Whether to include an explicit end marker in YAML encoding. If None, the default behavior is used.
            file_yaml_encode_version (tuple | None): The YAML version to use for encoding. If None, the default version is used.
            file_yaml_encode_tags (dict | None): Custom tags to use for YAML encoding. If None, no custom tags are applied.
            file_yaml_encode_sort_keys (bool | None): Whether to sort keys in the output. If None, the default behavior is used.
        """

        file_yaml_encode_loader: type[Loader] | Any
        file_yaml_encode_dumper: type[Dumper] | Any
        file_yaml_encode_default_style: str | None
        file_yaml_encode_default_flow_style: bool | None
        file_yaml_encode_canonical: bool | None
        file_yaml_encode_indent: int | None
        file_yaml_encode_width: int | None
        file_yaml_encode_allow_unicode: bool | None
        file_yaml_encode_line_break: str | None
        file_yaml_encode_explicit_start: bool | None
        file_yaml_encode_explicit_end: bool | None
        file_yaml_encode_version: tuple | None
        file_yaml_encode_tags: dict | None
        file_yaml_encode_sort_keys: bool | None

    @property
    def config(self) -> _InstanceConfig:
        return super().config

    @classmethod
    def _to_dict(cls, content: str, config: _InstanceConfig) -> dict:
        data = load(stream=content, Loader=config.file_yaml_encode_loader)
        return data

    def _from_dict(self, data: dict[str, Any], config: _InstanceConfig) -> str:
        content = dump(data=data,
                       Dumper=config.file_yaml_encode_dumper,
                       default_style=config.file_yaml_encode_default_style,
                       default_flow_style=config.file_yaml_encode_default_flow_style,
                       canonical=config.file_yaml_encode_canonical,
                       indent=config.file_yaml_encode_indent,
                       width=config.file_yaml_encode_width,
                       allow_unicode=config.file_yaml_encode_allow_unicode,
                       line_break=config.file_yaml_encode_line_break,
                       explicit_start=config.file_yaml_encode_explicit_start,
                       explicit_end=config.file_yaml_encode_explicit_end,
                       version=config.file_yaml_encode_version,
                       tags=config.file_yaml_encode_tags,
                       sort_keys=config.file_yaml_encode_sort_keys)
        return content
