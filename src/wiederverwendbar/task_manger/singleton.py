from wiederverwendbar.singleton import Singleton
from wiederverwendbar.task_manger.task_manager import TaskManager


class ManagerSingleton(TaskManager, metaclass=Singleton):
    ...
