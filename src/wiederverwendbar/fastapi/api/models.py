from typing import Optional

from pydantic import BaseModel, Field

from wiederverwendbar.pydantic.types.version import Version


class InfoModel(BaseModel):
    title: str = Field(..., title="Title", description="The title of the application.")
    description: str = Field(..., title="Description", description="The description of the application.")
    version: Version = Field(..., title="Version", description="The version of the application.")

    class Contact(BaseModel):
        name: str = Field(..., title="Name", description="The name of the contact.")
        email: str = Field(..., title="Email", description="The email of the contact.")

    contact: Optional[Contact] = Field(None, title="Contact", description="The contact of the application.")

    class LicenseInfo(BaseModel):
        name: str = Field(..., title="Name", description="The name of the license.")
        url: str = Field(..., title="URL", description="The URL of the license.")

    license_info: Optional[LicenseInfo] = Field(None, title="License Info", description="The license info of the application.")
    terms_of_service: Optional[str] = Field(None, title="Terms of Service", description="The terms of service of the application.")
