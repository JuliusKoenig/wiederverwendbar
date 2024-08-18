from typing import Union

from starlette.requests import Request
from starlette_admin.contrib.mongoengine.view import ModelView as StarletteAdminModelView

from wiederverwendbar.starlette_admin.mongoengine.auth.documents.acl import AccessControlList
from wiederverwendbar.starlette_admin.mongoengine.auth.views.base import BaseView


class ModelView(BaseView, StarletteAdminModelView):
    async def is_action_allowed(self, request: Request, name: str) -> bool:
        # check if action is allowed by super
        result = await super().is_action_allowed(request=request, name=name)
        if not result:
            return False

        # get acls
        acls = self.admin.acl_base_logic(view=self, request=request)
        if type(acls) is bool:  # admin case
            return acls
        if len(acls) == 0:  # no acl is set to this view for user
            return False

        # handle default actions
        if name == "delete":
            return self.can_delete(request, acls=acls)

        # get view identity
        identity = self.admin.view_identity_mapping[self]

        # check if action is allowed by acls
        for acl in acls:
            if acl.allow_execute:
                if len(acl.specify_actions) == 0:
                    return True
                else:
                    if f"{identity}.{name}" in acl.specify_actions:
                        return True
        return False

    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        # check if action is allowed by super
        result = await super().is_action_allowed(request=request, name=name)
        if not result:
            return False

        # get acls
        acls = self.admin.acl_base_logic(view=self, request=request)
        if type(acls) is bool:  # admin case
            return acls
        if len(acls) == 0:  # no acl is set to this view for user
            return False

        # handle default actions
        if name == "view":
            return self.can_view_details(request, acls=acls)
        elif name == "edit":
            return self.can_edit(request, acls=acls)
        elif name == "delete":
            return self.can_delete(request, acls=acls)

        # get view identity
        identity = self.admin.view_identity_mapping[self]

        # check if action is allowed by acls
        for acl in acls:
            if acl.allow_execute:
                if len(acl.specify_actions) == 0:
                    return True
                else:
                    if f"{identity}.{name}" in acl.specify_actions:
                        return True
        return False

    def can_view_details(self, request: Request, acls: Union[None, list[AccessControlList]] = None) -> bool:
        # check if action is allowed by super
        result = super().can_view_details(request=request)
        if not result:
            return False

        # get acls
        if acls is None:
            acls = self.admin.acl_base_logic(view=self, request=request)
        if type(acls) is bool:  # admin case
            return acls
        if len(acls) == 0:  # no acl is set to this view for user
            return False

        # check if action is allowed by acls
        for acl in acls:
            if acl.allow_detail:
                return True
        return False

    def can_create(self, request: Request, acls: Union[None, list[AccessControlList]] = None) -> bool:
        # check if action is allowed by super
        result = super().can_create(request=request)
        if not result:
            return False

        # get acls
        if acls is None:
            acls = self.admin.acl_base_logic(view=self, request=request)
        if type(acls) is bool:
            return acls  # admin case
        if len(acls) == 0:
            return False  # no acl is set to this view for user

        # check if view details is allowed
        can_view_details = self.can_view_details(request, acls=acls)
        if not can_view_details:
            return False

        # check if action is allowed by acls
        for acl in acls:
            if acl.allow_create:
                return True
        return False

    def can_edit(self, request: Request, acls: Union[None, list[AccessControlList]] = None) -> bool:
        # check if action is allowed by super
        result = super().can_edit(request=request)
        if not result:
            return False

        # get acls
        if acls is None:
            acls = self.admin.acl_base_logic(view=self, request=request)
        if type(acls) is bool:
            return acls  # admin case
        if len(acls) == 0:
            return False  # no acl is set to this view for user

        # check if view details is allowed
        can_view_details = self.can_view_details(request, acls=acls)
        if not can_view_details:
            return False

        # check if action is allowed by acls
        for acl in acls:
            if acl.allow_update:
                return True
        return False

    def can_delete(self, request: Request, acls: Union[None, list[AccessControlList]] = None) -> bool:
        # check if action is allowed by super
        result = super().can_delete(request=request)
        if not result:
            return False

        # get acls
        acls = self.admin.acl_base_logic(view=self, request=request)
        if type(acls) is bool:
            return acls  # admin case
        if len(acls) == 0:
            return False  # no acl is set to this view for user

        # check if action is allowed by acls
        for acl in acls:
            if acl.allow_delete:
                return True
        return False
