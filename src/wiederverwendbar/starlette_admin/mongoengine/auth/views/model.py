import logging
from typing import Sequence, Any, Union, Optional

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette_admin import RequestAction
from starlette_admin.contrib.mongoengine.view import ModelView as StarletteAdminModelView
from mongoengine import Document, ValidationError
from watchfiles import awatch

from wiederverwendbar.starlette_admin.mongoengine.auth.documents.acl import AccessControlList
from wiederverwendbar.starlette_admin.mongoengine.auth.views.base import BaseView

logger = logging.getLogger(__name__)


class ModelView(BaseView, StarletteAdminModelView):
    async def is_action_allowed(self, request: Request, name: str) -> bool:
        # check if action is allowed by super
        result = await super().is_action_allowed(request=request, name=name)
        if not result:
            return False

        # get acls
        acls = await self.admin.is_action_allowed(view=self, request=request, name=name)
        if type(acls) is bool:
            return acls
        return True

    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        # check if action is allowed by super
        result = await super().is_row_action_allowed(request=request, name=name)
        if not result:
            return False

        # get acls
        acls = await self.admin.is_row_action_allowed(view=self, request=request, name=name)
        if type(acls) is bool:
            return acls
        return True

    def can_view_details(self, request: Request) -> bool:
        # check if action is allowed by super
        result = super().can_view_details(request=request)
        if not result:
            return False

        # get acls
        acls = self.admin.can_view_details(view=self, request=request)
        if type(acls) is bool:  # admin case
            return acls
        return True

    def can_create(self, request: Request) -> bool:
        # check if action is allowed by super
        result = super().can_create(request=request)
        if not result:
            return False

        # get acls
        acls = self.admin.can_create(view=self, request=request)
        if type(acls) is bool:
            return acls
        return True

    def can_edit(self, request: Request) -> bool:
        # check if action is allowed by super
        result = super().can_edit(request=request)
        if not result:
            return False

        # get acls
        acls = self.admin.can_edit(view=self, request=request)
        if type(acls) is bool:
            return acls
        return True

    def can_delete(self, request: Request) -> bool:
        # check if action is allowed by super
        result = super().can_delete(request=request)
        if not result:
            return False

        # get acls
        acls = self.admin.can_delete(view=self, request=request)
        if type(acls) is bool:
            return acls
        return True

    async def filter_by_acls(self, request: Request, acls: list[AccessControlList], objects: Union[Document, Sequence[Document]]) -> Union[Document, Sequence[Document]]:
        # get objects of each acl
        acls_objects = []
        for acl in acls:
            try:
                acl_objects = list(self.document.objects(**acl.query_filter))
                acls_objects.extend(acl_objects)
            except ValidationError as e:
                logger.error(f"Acl query filter is not valid: {acl.name}\n"
                             f"Query filter: {acl.query_filter}\n"
                             f"Error: {e}")
                continue

        # filter objects by acls
        if isinstance(objects, Document):
            if objects in acls_objects:
                return objects
            else:
                raise HTTPException(status_code=403, detail="The requested object is filtered by acls.")
        else:
            result = []
            for obj in objects:
                if obj in acls_objects:
                    result.append(obj)
            return result

    async def get_request_action(self, request: Request) -> RequestAction:
        # get current path
        current_path = request.url.path

        # check if admin base url is in path
        if self.admin.base_url not in current_path:
            raise RuntimeError("Admin base url not found in request path.")
        current_path = current_path.replace(self.admin.base_url, "")

        # check if identity is in path
        identity_path = f"/{self.identity}/"
        if identity_path not in current_path:
            raise RuntimeError("Identity not found in request path.")
        current_path = current_path.replace(identity_path, "")

        # get request action
        if current_path.startswith("detail"):
            request_action = RequestAction.DETAIL
        elif current_path.startswith("edit"):
            request_action = RequestAction.EDIT
        else:
            raise RuntimeError("Request action not found.")

        return request_action

    async def count(self, request: Request, where: Union[dict[str, Any], str, None] = None) -> int:
        # build query
        q = await self._build_query(request, where)

        # get objects
        result = self.document.objects(q)

        # get acls
        acls = self.admin.is_accessible(view=self, request=request)
        if type(acls) is bool:
            if acls:
                return len(result)  # admin case
            else:
                return 0

        # filter by acls
        result = len(await self.filter_by_acls(request=request, acls=acls, objects=result))

        return result

    async def find_all(self,
                       request: Request,
                       skip: int = 0,
                       limit: int = 100,
                       where: Union[dict[str, Any], str, None] = None,
                       order_by: Optional[list[str]] = None) -> Sequence[Any]:
        result = await super().find_all(request=request, skip=skip, limit=limit, where=where, order_by=order_by)

        # get acls
        acls = self.admin.is_accessible(view=self, request=request)
        if type(acls) is bool:
            if acls:
                return result  # admin case
            else:
                return []

        # filter by acls
        result = await self.filter_by_acls(request=request, acls=acls, objects=result)

        return result

    async def find_by_pk(self, request: Request, pk: Any) -> Optional[Document]:
        result = await super().find_by_pk(request=request, pk=pk)
        if result is None:
            return result

        # get request action
        request_action = await self.get_request_action(request=request)

        # get acls
        if request_action is RequestAction.DETAIL:
            acls = self.admin.can_view_details(view=self, request=request)
        elif request_action is RequestAction.EDIT:
            acls = self.admin.can_edit(view=self, request=request)
        else:
            raise RuntimeError("Request action not not implemented for find_by_pk.")
        if type(acls) is bool:
            if acls:
                return result  # admin case
            else:
                return None

        # filter by acls
        result = await self.filter_by_acls(request=request, acls=acls, objects=result)

        return result

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Document]:
        result = await super().find_by_pks(request=request, pks=pks)

        # get acls
        acls = self.admin.is_accessible(view=self, request=request)
        if type(acls) is bool:
            if acls:
                return result
            else:
                return []

        # filter by acls
        result = await self.filter_by_acls(request=request, acls=acls, objects=result)

        return result

    async def delete(self, request: Request, pks: list[Any]) -> Optional[int]:
        # get objects
        objs = self.document.objects(id__in=pks)

        # get acls
        acls = self.admin.can_delete(view=self, request=request)
        if type(acls) is bool:
            if not acls:
                raise HTTPException(status_code=403, detail="The requested object is filtered by acls.")

        # filter by acls
        deletable_objs = await self.filter_by_acls(request=request, acls=acls, objects=objs)

        # get forbidden objects
        forbidden_objs = list(set(objs) - set(deletable_objs))

        # execute before_delete
        for obj in deletable_objs:
            await self.before_delete(request, obj)

        # delete objects
        deleted_count = None
        for obj in objs:
            # check if object is in forbidden objects
            if obj not in forbidden_objs:
                obj.delete()
                if deleted_count is None:
                    deleted_count = 0
                deleted_count += 1
                await self.after_delete(request, obj)
            else:
                logger.warning(f"Object deletion forbidden by acls: {obj.id}")

        return deleted_count
