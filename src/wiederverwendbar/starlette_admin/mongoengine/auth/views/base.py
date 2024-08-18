from starlette.requests import Request

from starlette_admin.base import BaseView as StarletteAdminBaseView


class BaseView(StarletteAdminBaseView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.admin = None

    def is_accessible(self, request: Request) -> bool:
        result = super().is_accessible(request)
        if not result:
            return False

        acls = self.admin.is_accessible(view=self, request=request)
        if type(acls) is bool:
            return acls
        return True
