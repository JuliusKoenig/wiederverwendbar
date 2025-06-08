import inspect
import re
from pathlib import Path
from typing import Optional, Union

DEBUGGER_FILENAME_PARTS = [r".*/python-ce/helpers/pydev/.*"]


def get_enter_frame(stack: Optional[list[inspect.FrameInfo]] = None, deep: int = 1) -> inspect.FrameInfo:
    if stack is None:
        stack = inspect.stack()

    last_frame_info = stack[0]
    for frame_info in stack[deep:]:
        if is_frame_in_debugger(frame_info=frame_info):
            return last_frame_info
        last_frame_info = frame_info
    return last_frame_info


def is_frame_in_debugger(frame_info: inspect.FrameInfo) -> bool:
    frame_filename = frame_info.filename.replace("\\", "/")
    for debugger_filename_part in DEBUGGER_FILENAME_PARTS:
        if re.match(debugger_filename_part, frame_filename):
            return True
    return False
