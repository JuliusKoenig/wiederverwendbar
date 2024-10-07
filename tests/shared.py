import logging
import time

from wiederverwendbar.logger import LoggerSingleton, LoggerSettings
from wiederverwendbar.mongoengine import MongoengineDbSingleton

from tests.task_manager import Manager, Worker, ScheduledTask

# init logging
LoggerSingleton(name="test", settings=LoggerSettings(log_level="DEBUG"), ignored_loggers_like=["pymongo"], init=True)

# init database
MongoengineDbSingleton(init=True)

manager = Manager()

logger = logging.getLogger(__name__)


@manager.register_task()
def task1(start: int, end: int = 10):
    # worker = Worker()
    # task = ScheduledTask()
    logger.info(f"Count from {start} to {end}")
    for i in range(start, end + 1):
        logger.info(i)
        time.sleep(1)
    logger.info("Done.")
