import time

from celery_test.app import app
from celery_test.tasks.base import BaseTask


@app.task(bind=True)
def wait(self: BaseTask, seconds: int):
    self.test()
    print(f"Wait(A) {seconds} seconds ...")
    for i in range(seconds):
        print(f"Wait(A): {i}")
        self.update_state(state="PROGRESS", meta={"progress": i})
        time.sleep(1)
