from dataclasses import dataclass
from typing import List, Optional

from starlette.requests import Request
from starlette_admin import RequestAction
from starlette_admin.fields import BooleanField

@dataclass
class BooleanAlsoField(BooleanField):
    also: str = ""

    def additional_js_links(self, request: Request, action: RequestAction) -> List[str]:
        additional_js_links = super().additional_js_links(request, action)
        if action.is_form():
            additional_js_links.append(
                str(
                    request.url_for(
                        f"{request.app.state.ROUTE_NAME}:statics",
                        path="js/boolean_also_field.js",
                    )
                )
            )

        return additional_js_links
