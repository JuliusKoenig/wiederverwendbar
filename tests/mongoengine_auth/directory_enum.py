import enum
from pathlib import Path
from typing import Union

# DynamicEnum = enum.Enum('DynamicEnum', {'foo': 42, 'bar': 24})
#
# foo = DynamicEnum(42)
# bar = DynamicEnum(24)


def DirectoryEnum(path: Union[str, Path]):
    if type(path) is str:
        path = Path(path)
    path = path.resolve()

    value = "DirectoryEnum"#_" + str(path).replace('/', '_').replace('\\', '_')

    if not path.is_dir():
        raise ValueError(f"Path '{path.absolute()}' is not a directory")

    names = {}
    for file in path.iterdir():
        if file.name.startswith("_"):
            continue

        if file.is_file():
            names[file.stem] = str(file.relative_to(path))

    return enum.Enum(value, names)


FileEnum = DirectoryEnum(path="statics/company_logo")

init_file = FileEnum("qwe.txt")

print()
