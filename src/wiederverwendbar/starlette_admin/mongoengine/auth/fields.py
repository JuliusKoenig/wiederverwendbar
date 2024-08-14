from typing import Any

from starlette.requests import Request
from starlette_admin.fields import EnumField


class AccessControlListReferenceField(EnumField):
    def _get_label(self, value: Any, request: Request) -> Any:
        for v, label in self._get_choices(request):
            if value == v:
                return label
        return "Unbekannte ACL-Referenz"
