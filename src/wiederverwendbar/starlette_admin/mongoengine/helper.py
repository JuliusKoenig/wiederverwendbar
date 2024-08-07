from typing import Union, Optional

from mongoengine import GridFSProxy, ImageGridFsProxy
from starlette.requests import Request


def get_grid_fs_url(file: Union[GridFSProxy, ImageGridFsProxy], request: Request, use_thumbnail: bool = True) -> Optional[str]:
    grid_id = file.grid_id
    if use_thumbnail and getattr(file, "thumbnail_id", None):
        grid_id = file.thumbnail_id
    if grid_id is None:
        return None
    url = request.url_for(
        request.app.state.ROUTE_NAME + ":api:file",
        db=file.db_alias,
        col=file.collection_name,
        pk=grid_id,
    )
    url_str = str(url)
    return url_str
