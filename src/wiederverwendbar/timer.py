import asyncio
import threading
import time
from typing import Union

_TIMERS: dict[str, float] = {}
_lock = threading.Lock()


def timer(name: str, seconds: Union[float, int]) -> bool:
    global _TIMERS

    seconds = float(seconds)

    if name not in _TIMERS:
        with _lock:
            _TIMERS[name] = time.perf_counter() + seconds
        wait = True
    else:
        with _lock:
            delta = time.perf_counter() - _TIMERS[name]
        wait = delta < 0
    if wait:
        ...
    else:
        clear_timer(name=name)
    return wait


def timer_loop(name: str, seconds: Union[float, int], loop_delay: float = 0.001) -> None:
    while timer(name, seconds):
        time.sleep(loop_delay)


async def timer_loop_async(name: str, seconds: Union[float, int], loop_delay: float = 0.001) -> None:
    while timer(name, seconds):
        await asyncio.sleep(loop_delay)


def clear_timer(name: str) -> None:
    global _TIMERS
    if name in _TIMERS:
        with _lock:
            del _TIMERS[name]


def clear_all_timers() -> None:
    global _TIMERS
    with _lock:
        _TIMERS = {}


if __name__ == '__main__':
    try:
        while True:
            print(time.time())
            timer_loop("test-loop", 1)
    except KeyboardInterrupt:
        ...

    print("end")
