import inspect
from functools import wraps

import typer


def typer_resolve_defaults(func):
    """
    This decorator resolves the default values of typer models.
    :param func: Function to decorate
    :return: Decorated function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get the function signature
        func_signature = inspect.signature(func)

        # Bind the arguments to the function signature
        bound_params = func_signature.bind(*args, **kwargs).arguments

        for param_name, param in func_signature.parameters.items():
            if param_name in bound_params:
                continue
            if param.default == param.empty:
                continue
            if type(param.default) not in [typer.models.ArgumentInfo, typer.models.OptionInfo]:
                continue
            if param.default.default_factory is not None:
                bound_params[param_name] = param.default.default_factory()
                continue
            if param.default.default is not Ellipsis:
                bound_params[param_name] = param.default.default
                continue
        return func(**bound_params)

    return wrapper
