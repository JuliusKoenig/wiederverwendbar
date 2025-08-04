import importlib.util
import sys
from types import ModuleType
from typing import Any, Union
from pydantic import BaseModel, Field

from wiederverwendbar.default import Default
from wiederverwendbar.pydantic.types.version import Version


class BrandingSettings(BaseModel):
    branding_title: Union[None, Default, str] = Field(default=Default(), title="Branding Title", description="Branding title.")
    branding_description: Union[None, Default, str] = Field(default=Default(), title="Branding Description", description="Branding description.")
    branding_version: Union[None, Default, Version] = Field(default=Default(), title="Branding Version", description="Branding version.")
    branding_author: Union[None, Default, str] = Field(default=Default(), title="Branding Author", description="Branding author.")
    branding_author_email: Union[None, Default, str] = Field(default=Default(), title="Branding Author Email", description="Branding author email.")
    branding_license: Union[None, Default, str] = Field(default=Default(), title="Branding License Name", description="Branding license name.")
    branding_license_url: Union[None, Default, str] = Field(default=Default(), title="Branding License URL", description="Branding license URL.")
    branding_terms_of_service: Union[None, Default, str] = Field(default=Default(), title="Branding Terms of Service", description="Branding terms of service.")

    def __init_subclass__(cls, module: Union[ModuleType, str, None] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if module is None:
            # use __main__ module
            module = sys.modules["__main__"]
        elif isinstance(module, str):
            # import module by name
            module = importlib.import_module(module)
        elif not isinstance(module, ModuleType):
            raise TypeError(f"Expected a module or module name, got {type(module)}")
        cls._branding_module = module

    def model_post_init(self, context: Any, /):
        branding_module = getattr(self, "_branding_module", None)
        if branding_module is not None:
            for key, target_type, module_key in [("branding_title", str, "__title__"),
                                    ("branding_description", str, "__description__"),
                                    ("branding_version", Version, "__version__"),
                                    ("branding_author", str, "__author__"),
                                    ("branding_author_email", str, "__author_email__"),
                                    ("branding_license", str, "__license__"),
                                    ("branding_license_url", str, "__license_url__"),
                                    ("branding_terms_of_service", str, "__terms_of_service__")]:
                # check if the branding module has the attribute
                if not hasattr(branding_module, module_key):
                    continue

                # get the value from the branding module
                module_value = getattr(branding_module, module_key)

                # cast the value to the target type if necessary
                if not isinstance(module_value, target_type):
                    module_value = target_type(module_value)

                # set the value if it is a Default
                if isinstance(getattr(self, key), Default):
                    setattr(self, key, module_value)
        super().model_post_init(context)

