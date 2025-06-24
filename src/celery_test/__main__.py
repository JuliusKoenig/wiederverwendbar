from celery_test.tasks import wait


def on_raw_message(body):
    print(body)


if __name__ == '__main__':
    result = wait.apply_async(kwargs={"seconds": 300})
    print(result.get(on_message=on_raw_message, propagate=False))
