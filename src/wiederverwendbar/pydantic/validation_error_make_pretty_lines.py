from pydantic import ValidationError


def validation_error_make_pretty_lines(exception: ValidationError) -> list[str]:
    """
    Make a ValidationError pretty by converting it to a list of strings.
    Each string represents one error in the ValidationError.

    :param exception: ValidationError: The ValidationError to be converted.
    :return: list[str]: A list of strings representing the errors.
    """

    errors = exception.errors()
    lines = []
    for error in errors:
        loc_str = ""
        for l in error.get("loc", ()):
            if isinstance(l, int):
                loc_str += f"[{l}]"
            else:
                if loc_str:
                    loc_str += "."
                loc_str += str(l)
        msg = error.get("msg", "")
        typ = error.get("type", "")
        line = f"Error at '{loc_str}': {msg} (type={typ})"
        lines.append(line)
    return lines
