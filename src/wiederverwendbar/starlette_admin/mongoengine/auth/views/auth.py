from typing import Optional, List, Union, Type

from starlette_admin.views import BaseView

from wiederverwendbar.starlette_admin.drop_down_icon_view.views import DropDownIconView


class AuthView(DropDownIconView):
    def __init__(self,
                 label: Optional[str] = None,
                 views: Optional[List[Union[Type[BaseView], BaseView]]] = None,
                 icon: Optional[str] = None,
                 always_open: Optional[bool] = None,
                 show_icon_on_sub_views: Optional[bool] = None
                 ):
        # set default values
        label = label or "Authentifizierung"
        views = views or []
        icon = icon or "fa fa-lock"
        if always_open is None:
            always_open = False
        if show_icon_on_sub_views is None:
            show_icon_on_sub_views = True

        super().__init__(label=label, views=views, icon=icon, always_open=always_open, show_icon_on_sub_views=show_icon_on_sub_views)
