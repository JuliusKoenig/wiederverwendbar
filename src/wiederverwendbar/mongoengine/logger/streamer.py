import atexit
import threading
import time
from datetime import datetime
from typing import Optional

from wiederverwendbar.functions.datetime import local_now
from wiederverwendbar.mongoengine.logger.documets import MongoengineLogDocument


class MongoengineLogStreamer(threading.Thread):
    def __init__(self,
                 log_document: type[MongoengineLogDocument],
                 search: Optional[dict] = None,
                 to: Optional[callable] = None,
                 name: Optional[str] = None,
                 begin: Optional[datetime] = None,
                 stream_rate: Optional[float] = None):
        if name is None:
            name = self.__class__.__name__
        super().__init__(name=name, daemon=True)
        self._lock = threading.Lock()

        if not issubclass(log_document, MongoengineLogDocument):
            raise TypeError(f"Expected '{MongoengineLogDocument.__name__}', got '{log_document}'.")
        self._log_document = log_document
        if search is None:
            search = {}
        if not isinstance(search, dict):
            raise TypeError(f"Expected 'dict', got '{type(search)}'.")
        self._search = search
        if to is None:
            to = mongoengine_log_stream_print
        if not callable(to):
            raise TypeError(f"Expected 'callable', got '{type(to)}'.")
        self._to = to
        if begin is None:
            begin = local_now()
        self._timestamp = begin
        if stream_rate is None:
            stream_rate = 0.001
        self._stream_rate = stream_rate
        self._buffer: list[dict] = []
        self._stopper = threading.Event()

        atexit.register(self.close)

    def __del__(self):
        self.close()

    def __enter__(self) -> 'MongoengineLogStreamer':
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def timestamp(self) -> datetime:
        with self._lock:
            return self._timestamp

    @timestamp.setter
    def timestamp(self, value: datetime):
        with self._lock:
            self._timestamp = value

    @property
    def stream_rate(self) -> float:
        with self._lock:
            return self._stream_rate

    @stream_rate.setter
    def stream_rate(self, value: float):
        with self._lock:
            self._stream_rate = value

    def _fetch(self) -> bool:
        entries = []
        for log_document in self._log_document.objects(timestamp__gt=self.timestamp, **self._search):
            log_document: MongoengineLogDocument
            for entry in log_document.entries:
                entries.append(entry)
            self.timestamp = log_document.timestamp
        with self._lock:
            self._buffer.extend(entries)
            return bool(self._buffer)

    def _stream(self):
        with self._lock:
            while self._buffer:
                entry = self._buffer.pop(0)
                self._to(entry)

    def run(self):
        while not self._stopper.is_set():
            self._fetch()
            self._stream()

            time.sleep(self.stream_rate)
        if self._fetch():  # fetch the last entries
            self._stream()

    def close(self):
        self._stopper.set()


def mongoengine_log_stream_print(entry: dict):
    if "message" in entry:
        print(entry["message"])
    else:
        raise ValueError(f"Expected 'message' in '{entry}'.")
