from starlette_admin.base import CustomView as StarletteAdminCustomView

from wiederverwendbar.starlette_admin.mongoengine.auth.views.base import BaseView


class CustomView(BaseView, StarletteAdminCustomView):
    ...
