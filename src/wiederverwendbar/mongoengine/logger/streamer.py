import atexit
import threading
import time
from datetime import datetime
from typing import Optional

from wiederverwendbar.functions.datetime import local_now
from wiederverwendbar.mongoengine.logger.documets import MongoengineLogDocument


class MongoengineLogStreamer(threading.Thread):
    def __init__(self, log_document: type[MongoengineLogDocument], to: Optional[callable] = None, name: Optional[str] = None, begin: Optional[datetime] = None):
        if name is None:
            name = self.__class__.__name__
        super().__init__(name=name, daemon=True)

        if not issubclass(log_document, MongoengineLogDocument):
            raise TypeError(f"Expected '{MongoengineLogDocument.__name__}', got '{log_document}'.")
        self._log_document = log_document
        if to is None:
            to = mongoengine_log_stream_print
        if not callable(to):
            raise TypeError(f"Expected 'callable', got '{type(to)}'.")
        self._to = to
        if begin is None:
            begin = local_now()
        self._timestamp = begin
        self._stopper = threading.Event()

        atexit.register(self.stop)

        self.start()

    def __del__(self):
        self.stop()

    def __enter__(self) -> 'MongoengineLogStreamer':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def run(self):
        while not self._stopper.is_set():
            for log_document in self._log_document.objects(timestamp__gt=self._timestamp):
                log_document: MongoengineLogDocument
                for entry in log_document.entries:
                    self._to(entry)
                self._timestamp = log_document.timestamp
            time.sleep(0.001)

    def stop(self):
        self._stopper.set()


def mongoengine_log_stream_print(entry: dict):
    if "message" in entry:
        print(entry["message"])
    else:
        raise ValueError(f"Expected 'message' in '{entry}'.")
