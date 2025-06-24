from celery import group
from celery.result import AsyncResult
from celery_test.tasks import wait


def on_raw_message(body):
    print(body)


if __name__ == '__main__':
    result = wait.apply_async((300,))
    # task_id = '043beb9a-eaa7-4686-9f94-14b6f7c50fda'
    # result = AsyncResult(task_id)
    # result: AsyncResult = wait_c.delay(300)
    print(result.get())
    # print(result.get(on_message=on_raw_message, propagate=False))
    # print(group(wait.s(seconds=100) for _ in range(5)).apply_async().get(on_message=on_raw_message, propagate=False))
