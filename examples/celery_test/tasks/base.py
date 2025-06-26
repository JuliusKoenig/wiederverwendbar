from celery import Task


class BaseTask(Task):
    def test(self):
        print("test123")
