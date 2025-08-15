from wiederverwendbar.pydantic.file_config.base import FileConfig


class JsonFileConfig(FileConfig):
    @classmethod
    @register_loader("json", default_suffix=".json")
    def _load_json(cls, content: str, **kwargs) -> dict[str, Any]:
        return json.loads(content, **kwargs)

    @register_saver("json")
    def _save_json(self, data: dict[str, Any], **kwargs) -> str:
        return json.dumps(data, **kwargs)
