class FileConfigError(Exception):
    ...


class FileConfigLoadingError(FileConfigError):
    ...


class FileConfigSavingError(FileConfigError):
    ...
