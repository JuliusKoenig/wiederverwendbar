from typing import Optional
from pydantic import BaseModel, Field


class BrandingSettings(BaseModel):
    branding_title: Optional[str] = Field(default=None, title="Branding Title", description="Branding title.")
    branding_description: Optional[str] = Field(default=None, title="Branding Description", description="Branding description.")
    branding_version: Optional[str] = Field(default=None, title="Branding Version", description="Branding version.")
    branding_author: Optional[str] = Field(default=None, title="Branding Author", description="Branding author.")
    branding_author_email: Optional[str] = Field(default=None, title="Branding Author Email", description="Branding author email.")
    branding_license_name: Optional[str] = Field(default=None, title="Branding License Name", description="Branding license name.")
    branding_license_url: Optional[str] = Field(default=None, title="Branding License URL", description="Branding license URL.")
    branding_terms_of_service: Optional[str] = Field(default=None, title="Branding Terms of Service", description="Branding terms of service.")
