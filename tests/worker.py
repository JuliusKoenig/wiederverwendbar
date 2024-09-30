import time

from tests.shared import manager

if __name__ == '__main__':
    worker = manager.create_worker("worker1")

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
