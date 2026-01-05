import logging

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.datastructures import State
from starlette_admin.base import BaseAdmin as _BaseAdmin

logger = logging.getLogger(__name__)



class BaseAdmin(_BaseAdmin):
    def mount_to(self, app: Starlette) -> None:
        super().mount_to(app)

        # get admin app
        admin_app = None
        for app in app.routes:
            if not isinstance(app, Mount):
                continue
            if app.name != self.route_name:
                continue
            admin_app = app.app
        if admin_app is None:
            raise ValueError("Admin app not found")

        # add admin to admin app
        admin_app.state.admin = self

    @classmethod
    def from_state(cls, state: State):
        admin = state.admin
        if not isinstance(admin, cls):
            raise ValueError(f"Admin is not instance of {cls}")
        return admin
