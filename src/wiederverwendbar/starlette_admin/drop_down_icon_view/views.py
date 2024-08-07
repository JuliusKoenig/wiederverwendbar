from typing import Optional, List, Union, Type

from starlette_admin.views import BaseView, DropDown


class DropDownIconView(DropDown):
    def __init__(
            self,
            label: str,
            views: List[Union[Type[BaseView], BaseView]],
            icon: Optional[str] = None,
            always_open: bool = True,
            show_icon_on_sub_views: bool = True
    ):
        super().__init__(label=label, views=views, icon=icon, always_open=always_open)

        self.show_icon_on_sub_views = show_icon_on_sub_views
