from tests.shared import manager

if __name__ == '__main__':
    task = manager.schedule_task("task1", start=1, end=20)
    with task.log_streamer():
        task.wait_for_end()
