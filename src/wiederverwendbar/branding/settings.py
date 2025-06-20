import importlib.util
import sys
from pathlib import Path
from typing import Optional, Any, Union
from pydantic import BaseModel, Field, computed_field

from wiederverwendbar.default import Default


class BrandingSettings(BaseModel):
    branding_title: Union[None, Default, str] = Field(default=Default(), title="Branding Title", description="Branding title.")
    branding_description: Union[None, Default, str] = Field(default=Default(), title="Branding Description", description="Branding description.")
    branding_version: Union[None, Default, str] = Field(default=Default(), title="Branding Version", description="Branding version.")
    branding_author: Union[None, Default, str] = Field(default=Default(), title="Branding Author", description="Branding author.")
    branding_author_email: Union[None, Default, str] = Field(default=Default(), title="Branding Author Email", description="Branding author email.")
    branding_license: Union[None, Default, str] = Field(default=Default(), title="Branding License Name", description="Branding license name.")
    branding_license_url: Union[None, Default, str] = Field(default=Default(), title="Branding License URL", description="Branding license URL.")
    branding_terms_of_service: Union[None, Default, str] = Field(default=Default(), title="Branding Terms of Service", description="Branding terms of service.")

    def model_post_init(self, context: Any, /):
        # get attributes from __main__ module
        main_module = sys.modules["__main__"]
        module_data = self.get_attributes(main_module.__dict__)
        if module_data is None:
            # ToDO: this code is not working for pyprojects.toml [project.scripts]
            init_file = Path(main_module.__file__).parent / "__init__.py"
            if init_file.is_file():
                init_file_module_spec = importlib.util.spec_from_file_location("__main__.__init__", init_file)
                init_file_module = importlib.util.module_from_spec(init_file_module_spec)
                sys.modules["__main__.__init__"] = init_file_module
                init_file_module_spec.loader.exec_module(init_file_module)
                module_data = self.get_attributes(init_file_module.__dict__)
        if module_data is None:
            module_data = {}

        for key in ["branding_title",
                    "branding_description",
                    "branding_version",
                    "branding_author",
                    "branding_author_email",
                    "branding_license",
                    "branding_license_url",
                    "branding_terms_of_service"]:
            value = module_data.get(key, None)
            if type(getattr(self, key)) is Default:
                setattr(self, key, value)

        super().model_post_init(context)

    @classmethod
    def get_attributes(cls, ns: dict[str, Any]) -> Optional[dict[str, str]]:
        found_something = False
        attributes = {}
        for key, module_key in {"branding_title": "__title__",
                                "branding_description": "__description__",
                                "branding_version": "__version__",
                                "branding_author": "__author__",
                                "branding_author_email": "__author_email__",
                                "branding_license": "__license__",
                                "branding_license_url": "__license_url__",
                                "branding_terms_of_service": "__terms_of_service__"}.items():
            if module_key in ns:
                found_something = True
                attributes[key] = ns[module_key]
        return attributes if found_something else None

    @computed_field(title="Branding Version Major", description="Branding version major.")
    @property
    def branding_version_major(self) -> Optional[int]:
        if self.branding_version is None:
            return None
        return int(self.branding_version.split(".")[0])

    @computed_field(title="Branding Version Minor", description="Branding version minor.")
    @property
    def branding_version_minor(self) -> Optional[int]:
        if self.branding_version is None:
            return None
        return int(self.branding_version.split(".")[1])

    @computed_field(title="Branding Version Patch", description="Branding version patch.")
    @property
    def branding_version_patch(self) -> Optional[int]:
        if self.branding_version is None:
            return None
        return int(self.branding_version.split(".")[2])
