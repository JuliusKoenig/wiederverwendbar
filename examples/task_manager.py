import logging
import time

from wiederverwendbar.task_manger import TaskManager, Task, AtManagerCreation, EverySeconds, Trigger, At, AtManagerStart, AtNow, EveryMinutes

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)


# create custom trigger
class MyTrigger(Trigger):
    def __init__(self):
        super().__init__()

        self.triggered = False

    def __str__(self):
        return f"{self.__class__.__name__}(triggered={self.triggered})"

    def check(self) -> bool:
        if self.triggered:
            return False
        self.triggered = True
        return True


# create manager
manager1 = TaskManager(name="Manager1", logger=logger)
manager2 = TaskManager(name="Manager2", logger=logger)


@manager1.task(AtManagerCreation(delay_for_seconds=10))
def task1():
    print("Manager1.Task1 ...")


@manager1.task(EverySeconds(2))
def task2():
    print("Manager1.Task2 ...")
    time.sleep(2)


@manager1.task(At(second=0), At(second=10), At(second=20), At(second=30), At(second=40), At(second=50))
def task3():
    print("Manager1.Task3 ...")
    time.sleep(4)


if __name__ == '__main__':
    logger.debug("This is the main module.")

    # start worker
    manager1.start()
    manager2.start()

    # create tasks
    manager2.add_task(Task(lambda: print("Manager2.Task1 ..."), AtManagerStart(delay_for_seconds=5)))
    manager2.add_task(Task(lambda: print("Manager2.Task2 ..."), AtNow(delay_for_minutes=1)))
    manager2.add_task(Task(lambda: print("Manager2.Task3 ..."), EveryMinutes(1)))

    # enter the main loop
    try:
        while True:
            logger.debug("Main loop ...")
            # if worker count is 0
            # manager1.loop(stay_in_loop=False)
            # manager2.loop(stay_in_loop=False)
            time.sleep(1)
    except KeyboardInterrupt:
        logger.debug("Keyboard interrupt.")

    manager1.stop()
    # manager2.stop()
