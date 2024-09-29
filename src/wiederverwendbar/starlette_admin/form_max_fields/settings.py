from pydantic import Field

from wiederverwendbar.starlette_admin.settings.settings import AdminSettings


class FormMaxFieldsAdminSettings(AdminSettings):
    admin_form_max_fields: int = Field(default=1000, title="Form Max Fields", description="The maximum number of fields in a form.")
