import asyncio
import time
from typing import Any

from celery.result import AsyncResult

from celery_test.tasks import wait


def on_interval(*args, **kwargs):
    print(*args, **kwargs)


async def get(result: AsyncResult, timeout: float | None = None) -> Any:
    start = time.time()
    while result.state == "PROGRESS":
        print(result.result)

        if timeout is not None:
            if time.time() - start > timeout:
                raise TimeoutError("Operation timed out")

        await asyncio.sleep(1)


async def main():
    result: AsyncResult = wait.apply_async(kwargs={"seconds": 5})
    print(await get(result))


if __name__ == '__main__':
    asyncio.run(main())
