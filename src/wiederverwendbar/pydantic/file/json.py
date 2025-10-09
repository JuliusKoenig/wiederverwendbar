import json
from typing import Any, Callable

from wiederverwendbar.pydantic.file.base import BaseFile


class JsonFile(BaseFile):
    class Config:
        file_suffix = ".json"
        file_json_decoder_cls = None
        file_json_decode_object_hook = None
        file_json_decode_parse_float = None
        file_json_decode_parse_int = None
        file_json_decode_parse_constant = None
        file_json_decode_object_pairs_hook = None
        file_json_encode_skip_keys = False
        file_json_encode_ensure_ascii = True
        file_json_encode_check_circular = True
        file_json_encode_allow_nan = True
        file_json_encoder_cls = None
        file_json_encode_indent = None
        file_json_encode_separators = None
        file_json_encode_default = None
        file_json_encode_sort_keys = False

    class _InstanceConfig(BaseFile._InstanceConfig):
        """
        Instance configuration for json file handling.

        Attributes:
            file_dir (str | Path): Directory where the file is located. If a string is provided, it will be converted to a Path object.
            file_name (str | None): Name of the file without suffix. If None, the class name in snake_case will be used.
            file_suffix (str | None): File extension. If None, no suffix will be used.
            file_encoding (str | None): File encoding. If None, the system default will be used.
            file_newline (str | None): Newline character(s). If None, the system default will be used.
            file_overwrite (dict[str, Any] | None): Dictionary of values to overwrite after loading the file.
            file_must_exist (FILE_MUST_EXIST_ANNOTATION): Whether the file must exist. True means "yes_print", False means "no_ignore"
            file_save_on_load (FILE_SAVE_ON_LOAD_ANNOTATION): Whether to save the file upon loading if it does not exist.
            file_on_reading_error (FILE_ON_ERROR_ANNOTATION): Action to take on reading error.
            file_on_to_dict_error (FILE_ON_ERROR_ANNOTATION): Action to take on to_dict conversion error.
            file_on_validation_error (FILE_ON_ERROR_ANNOTATION): Action to take on validation error.
            file_on_from_dict_error (FILE_ON_ERROR_ANNOTATION): Action to take on from_dict conversion error.
            file_on_saving_dict_error (FILE_ON_ERROR_ANNOTATION): Action to take on saving dict error.
            file_console (Console): Console object for logging messages. If None, print statements will be used.
            file_include (set[int] | set[str] | Mapping[int, bool | Any] | Mapping[str, bool | Any] | None): Fields to include when saving.
            file_exclude (set[int] | set[str] | Mapping[int, bool | Any] | Mapping[str, bool | Any] | None): Fields to exclude when saving.
            file_context (Any | None): Context to pass to Pydantic serialization methods.
            file_by_alias (bool | None): Whether to use field aliases when saving.
            file_exclude_unset (bool): Whether to exclude unset fields when saving.
            file_exclude_defaults (bool): Whether to exclude fields with default values when saving.
            file_exclude_none (bool): Whether to exclude fields with None values when saving.

            file_json_decoder_cls (type[json.JSONDecoder] | None): Custom JSONDecoder class to use for decoding JSON content.
            file_json_decode_object_hook (Callable[[dict[Any, Any]], Any | None] | None): Function to transform decoded JSON objects (dictionaries).
            file_json_decode_parse_float (Callable[[str], Any | None] | None): Function to parse JSON float values.
            file_json_decode_parse_int (Callable[[str], Any | None] | None): Function to parse JSON integer values.
            file_json_decode_parse_constant (Callable[[str], Any | None] | None): Function to handle special JSON constants like NaN and Infinity.
            file_json_decode_object_pairs_hook (Callable[[list[tuple[Any, Any]]], Any | None] | None): Function to transform decoded JSON object pairs (list of tuples).
            file_json_encode_skip_keys (bool): Whether to skip keys that are not basic types (str, int, float, bool, None) during encoding.
            file_json_encode_ensure_ascii (bool): Whether to escape non-ASCII characters in the output JSON string.
            file_json_encode_check_circular (bool): Whether to check for circular references during encoding.
            file_json_encode_allow_nan (bool): Whether to allow NaN and Infinity values in the output JSON string.
            file_json_encoder_cls (type[json.JSONEncoder] | None): Custom JSONEncoder class to use for encoding Python objects to JSON.
            file_json_encode_indent (None | int | str): Indentation level for pretty-printing the output JSON string. If None, the most compact representation is used.
            file_json_encode_separators (tuple[str, str] | None): Tuple specifying how to separate items and key-value pairs in the output JSON string. If None, defaults to (', ', ': ').
            file_json_encode_default (Callable[[...], Any | None] | None): Function to handle objects that are not serializable by default.
            file_json_encode_sort_keys (bool): Whether to sort the keys in the output JSON string.
        """

        file_json_decoder_cls: type[json.JSONDecoder] | None
        file_json_decode_object_hook: Callable[[dict[Any, Any]], Any | None] | None
        file_json_decode_parse_float: Callable[[str], Any | None] | None
        file_json_decode_parse_int: Callable[[str], Any | None] | None
        file_json_decode_parse_constant: Callable[[str], Any | None] | None
        file_json_decode_object_pairs_hook: Callable[[list[tuple[Any, Any]]], Any | None] | None
        file_json_encode_skip_keys: bool
        file_json_encode_ensure_ascii: bool
        file_json_encode_check_circular: bool
        file_json_encode_allow_nan: bool
        file_json_encoder_cls: type[json.JSONEncoder] | None
        file_json_encode_indent: None | int | str
        file_json_encode_separators: tuple[str, str] | None
        file_json_encode_default: Callable[[...], Any | None] | None
        file_json_encode_sort_keys: bool

    @classmethod
    def _to_dict(cls, content: str, config: _InstanceConfig) -> dict:
        data = json.loads(content,
                          cls=config.file_json_decoder_cls,
                          object_hook=config.file_json_decode_object_hook,
                          parse_float=config.file_json_decode_parse_float,
                          parse_int=config.file_json_decode_parse_int,
                          parse_constant=config.file_json_decode_parse_constant,
                          object_pairs_hook=config.file_json_decode_object_pairs_hook)
        return data

    def _from_dict(self, data: dict[str, Any], config: _InstanceConfig) -> str:
        content = json.dumps(data,
                             skipkeys=config.file_json_encode_skip_keys,
                             ensure_ascii=config.file_json_encode_ensure_ascii,
                             check_circular=config.file_json_encode_check_circular,
                             allow_nan=config.file_json_encode_allow_nan,
                             cls=config.file_json_encoder_cls,
                             indent=config.file_json_encode_indent,
                             separators=config.file_json_encode_separators,
                             default=config.file_json_encode_default,
                             sort_keys=config.file_json_encode_sort_keys)
        return content
