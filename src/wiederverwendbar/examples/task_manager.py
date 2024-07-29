import logging
import time

from wiederverwendbar.task_manger import TaskManager, Task, AtCreation, EverySeconds

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)

# create manager
manager1 = TaskManager(name="Manager1", logger=logger)
manager2 = TaskManager(name="Manager2", logger=logger)


@manager1.task(name="Task 1", trigger=AtCreation(delay_for_seconds=10))
def task1():
    logger.debug("Task 1 ...")


@manager1.task(name="Task 2", trigger=EverySeconds(2))
def task2():
    logger.debug("Task 2 ...")
    time.sleep(2)


@manager1.task(name="Task 3", trigger=EverySeconds(4))
def task3():
    logger.debug("Task 3 ...")
    time.sleep(4)


if __name__ == '__main__':
    logger.debug("This is the main module.")

    # start worker
    manager1.start()
    manager2.start()

    # create tasks
    Task(name="Task 1", manager=manager2, trigger=AtCreation(delay_for_seconds=10), payload=task1)
    Task(name="Task 2", manager=manager2, trigger=EverySeconds(2), payload=task2)
    Task(name="Task 3", manager=manager2, trigger=EverySeconds(4), payload=task3)

    # enter main loop
    try:
        while True:
            logger.debug("Main loop ...")
            # Manager().loop()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.debug("Keyboard interrupt.")

    manager1.stop()
    manager2.stop()
