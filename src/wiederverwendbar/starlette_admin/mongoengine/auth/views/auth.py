from typing import Optional, List, Union, Type

from starlette_admin.views import BaseView, DropDown


class AuthView(DropDown):
    def __init__(self,
                 label: Optional[str] = None,
                 views: Optional[List[Union[Type[BaseView], BaseView]]] = None,
                 icon: Optional[str] = None,
                 always_open: Optional[bool] = None):
        # set default values
        label = label or "Authentifizierung"
        views = views or []
        icon = icon or "fa fa-lock"
        always_open = always_open or False

        super().__init__(label=label, views=views, icon=icon, always_open=always_open)
