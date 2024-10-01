from tests.shared import manager


if __name__ == '__main__':
    task = manager.schedule_task("task1", start=1, end=3)
    # task.wait_for_end(timeout=5)
    print("Task finished.")

