from starlette_admin.base import Link as StarletteAdminLink

from wiederverwendbar.starlette_admin.mongoengine.auth.views.base import BaseView


class Link(BaseView, StarletteAdminLink):
    ...
