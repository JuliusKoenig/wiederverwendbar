import json
from typing import Any

from wiederverwendbar.pydantic.file.base import BaseFile


class JsonFile(BaseFile):
    class Config:
        file_suffix = ".json"

    @classmethod
    def _to_dict(cls, content: str, config: BaseFile._InstanceConfig) -> dict:
        data = json.loads(content)
        return data

    def _from_dict(self, data: dict[str, Any], config: BaseFile._InstanceConfig) -> str:
        content = json.dumps(data,
                             sort_keys=config.file_sort_keys,
                             indent=config.file_indent)
        return content
