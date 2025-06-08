import importlib.util
import importlib.resources
import sys
from pathlib import Path
from typing import Optional, Any

from wiederverwendbar.branding.settings import BrandingSettings
from wiederverwendbar.inspect import get_enter_frame


class BrandingApp:
    def __init__(self,
                 title: Optional[str] = None,
                 description: Optional[str] = None,
                 version: Optional[str] = None,
                 author: Optional[str] = None,
                 author_email: Optional[str] = None,
                 license_name: Optional[str] = None,
                 license_url: Optional[str] = None,
                 terms_of_service: Optional[str] = None,
                 settings: Optional[BrandingSettings] = None,
                 stack_deep: int = 3):
        """
        Create a new Branding App.

        :param title: Title
        :param description: Description
        :param version: Version
        :param author: Author
        :param author_email: Author Email
        :param license_name: License Name
        :param license_url: License URL
        :param terms_of_service: Terms of Service URL
        :param settings: Branding Settings
        """

        # get attributes from __main__ module
        main_module = sys.modules["__main__"]
        attributes = self.get_attributes(main_module.__dict__)
        if attributes is None:
            init_file = Path(main_module.__file__).parent / "__init__.py"
            if init_file.is_file():
                init_file_module_spec = importlib.util.spec_from_file_location("__main__.__init__", init_file)
                init_file_module = importlib.util.module_from_spec(init_file_module_spec)
                sys.modules["__main__.__init__"] = init_file_module
                init_file_module_spec.loader.exec_module(init_file_module)
                attributes = self.get_attributes(init_file_module.__dict__)

        # define attributes
        settings = settings or BrandingSettings()
        self.branding_title = title or attributes.get("__title__", settings.branding_title)
        self.branding_description = description or attributes.get("__description__", settings.branding_description)
        self.branding_version = version or attributes.get("__version__", settings.branding_version)
        self.branding_author = author or attributes.get("__author__", settings.branding_author)
        self.branding_author_email = author_email or attributes.get("__author_email__", settings.branding_author_email)
        self.branding_license_name = license_name or attributes.get("__license_name__", settings.branding_license_name)
        self.branding_license_url = license_url or attributes.get("__license_url__", settings.branding_license_url)
        self.branding_terms_of_service = terms_of_service or attributes.get("__terms_of_service__", settings.branding_terms_of_service)


        print()

    @classmethod
    def get_attributes(cls, ns: dict[str, Any]) -> Optional[dict[str, str]]:
        found_something = False
        attributes = {}
        for key in ["__title__",
                    "__description__",
                    "__version__",
                    "__author__",
                    "__author_email__",
                    "__license_name__",
                    "__license_url__",
                    "__terms_of_service__"]:
            if key in ns:
                found_something = True
                attributes[key] = ns[key]
        return attributes if found_something else None
