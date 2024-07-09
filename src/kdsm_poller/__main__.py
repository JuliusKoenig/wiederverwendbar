import logging
import time

from kdsm_poller.task_manger import Manager, Task, AtCreation, Seconds

logger = logging.getLogger(__name__)

# create manager
manager1 = Manager(name="Manager1", logger=logger)
manager2 = Manager(name="Manager2", logger=logger)


@manager1.task(name="Task 1", trigger=AtCreation(delay_for_seconds=10), return_func=True)
@manager2.task(name="Task 1", trigger=AtCreation(delay_for_seconds=10), return_func=True)
def task1():
    logger.debug("Task 1 ...")


@manager1.task(name="Task 2", trigger=Seconds(2), return_func=True)
@manager2.task(name="Task 2", trigger=Seconds(2), return_func=True)
def task2():
    logger.debug("Task 2 ...")
    # time.sleep(2)


@manager1.task(name="Task 3", trigger=Seconds(4), return_func=True)
@manager2.task(name="Task 3", trigger=Seconds(4), return_func=True)
def task3():
    logger.debug("Task 3 ...")
    # time.sleep(4)


if __name__ == '__main__':
    logger.debug("This is the main module.")

    # start worker
    manager1.start()
    # manager2.start()

    # create tasks
    # Task(name="Task 1", manager=manager1, trigger=AtCreation(delay_for_seconds=10), payload=task1)
    # Task(name="Task 2", manager=manager1, trigger=Seconds(2), payload=task2)
    # Task(name="Task 3", manager=manager1, trigger=Seconds(4), payload=task3)
    # Task(name="Task 1", manager=manager2, trigger=AtCreation(delay_for_seconds=10), payload=task1)
    # Task(name="Task 2", manager=manager2, trigger=Seconds(2), payload=task2)
    # Task(name="Task 3", manager=manager2, trigger=Seconds(4), payload=task3)

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
