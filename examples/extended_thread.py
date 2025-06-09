import time
from typing import Union

from wiederverwendbar.threading import ExtendedThread



def test_watchdog(self: ExtendedThread):
    return True


def thread_target(*args, **kwargs):
    print("loop", args, kwargs)


if __name__ == '__main__':
    thread = ExtendedThread(name="test", target=thread_target, args=(1, 2), kwargs={"a": 1}, loop_sleep_time=1, watchdog_target=test_watchdog)

    while True:
        try:
            time.sleep(3)
            with thread.loop_wait():
                print("main thread")
                time.sleep(5)
        except KeyboardInterrupt:
            break
    # thread.stop()
    # thread.raise_exception(Exception("hallo welt"))
