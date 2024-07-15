from typing import Any, Dict

from starlette.requests import Request
from starlette_admin import action
from starlette_admin.contrib.mongoengine import ModelView as BaseModelView
from starlette_admin import RequestAction


class FixedModelView(BaseModelView):
    async def serialize(
            self,
            obj: Any,
            request: Request,
            action: RequestAction,
            include_relationships: bool = True,
            include_select2: bool = False,
    ) -> Dict[str, Any]:
        result = await super().serialize(obj, request, action, include_relationships, include_select2)
        result["id"] = str(result["id"])
        return result
