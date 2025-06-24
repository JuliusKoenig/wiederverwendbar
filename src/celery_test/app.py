import os

from celery import Celery

from celery_test import __name__ as __module_name__

app = Celery(__module_name__,
             include=[f"{__module_name__}.tasks"],
             task_cls=f"{__module_name__}.tasks.base:BaseTask")
app.conf.update(broker_url=os.environ.get("BROKER_URL",
                                          f"pyamqp://"
                                          f"{os.environ.get('BROKER_USERNAME', 'admin')}:"
                                          f"{os.environ.get('BROKER_PASSWORD', 'password')}@"
                                          f"{os.environ.get('BROKER_HOST', 'localhost')}//"),
                result_backend=os.environ.get("RESULT_BACKEND_URL",
                                              f"db+mysql+pymysql://"
                                              f"{os.environ.get('DB_USERNAME', 'admin')}:"
                                              f"{os.environ.get('DB_PASSWORD', 'password')}@"
                                              f"{os.environ.get('DB_HOST', 'localhost')}/"
                                              f"{os.environ.get('DB_DATABASE_NAME', 'test')}"),
                task_serializer="json",
                result_serializer="json",
                accept_content=["json"],
                timezone="Europe/Berlin",
                enable_utc=True)
