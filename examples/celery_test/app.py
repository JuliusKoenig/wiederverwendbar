import os

from celery import Celery

from celery_test import __name__ as __module_name__


def get_broker_url():
    return os.environ.get("BROKER_URL",
                          f"pyamqp://"
                          f"{os.environ.get('BROKER_USERNAME', 'admin')}:"
                          f"{os.environ.get('BROKER_PASSWORD', 'password')}@"
                          f"{os.environ.get('BROKER_HOST', 'localhost')}:"
                          f"{os.environ.get('BROKER_PORT', '5672')}//")


def get_db_url():
    return (f"mysql+pymysql://"
            f"{os.environ.get('DB_USERNAME', 'admin')}:"
            f"{os.environ.get('DB_PASSWORD', 'password')}@"
            f"{os.environ.get('DB_HOST', 'localhost')}:"
            f"{os.environ.get('DB_PORT', '3306')}/"
            f"{os.environ.get('DB_NAME', 'test')}")


def get_result_backend_url():
    return os.environ.get("RESULT_BACKEND_URL", f"db+{get_db_url()}")


app = Celery(__module_name__,
             include=[f"{__module_name__}.tasks"],
             task_cls=f"{__module_name__}.tasks.base:BaseTask")
app.conf.update(broker_url=get_broker_url(),
                result_backend=get_result_backend_url(),
                beat_scheduler="sqlalchemy_celery_beat.schedulers:DatabaseScheduler",
                beat_dburi=get_db_url(),
                task_serializer="json",
                result_serializer="json",
                accept_content=["json"],
                timezone="Europe/Berlin",
                enable_utc=True)
