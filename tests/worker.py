import time

from tests.shared import manager

if __name__ == '__main__':
    worker = manager.create_worker()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    # raise_exception = Exception("hallo welt")
    # worker.stop()
    # thread.raise_exception(Exception("hallo welt"))
