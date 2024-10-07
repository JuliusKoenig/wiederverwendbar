import atexit as _atexit
import logging as _logging
import threading as _threading
from itertools import count as _count
from typing import Optional as _Optional

from wiederverwendbar.functions.datetime import local_now as _local_now
from wiederverwendbar.mongoengine.logger.documets import MongoengineLogDocument as _MongoengineLogDocument
from wiederverwendbar.mongoengine.logger.formatters import MongoengineLogFormatter as _MongoengineLogFormatter

_counter = _count().__next__
_counter() # skip 0

class MongoengineLogHandler(_logging.Handler):
    def __init__(self,
                 level=_logging.NOTSET,
                 document: _Optional[type[_MongoengineLogDocument]] = None,
                 document_kwargs: _Optional[dict] = None,
                 buffer_size: _Optional[int] = None,
                 buffer_periodical_flush_timing: _Optional[float] = None,
                 buffer_early_flush_level: _Optional[int] = None):
        super().__init__(level=level)
        self.formatter: _MongoengineLogFormatter = _MongoengineLogFormatter()
        if document is None:
            document = _MongoengineLogDocument
        self._document: type[_MongoengineLogDocument] = document
        if document_kwargs is None:
            document_kwargs = {}
        self._document_kwargs: dict = document_kwargs
        self._buffer: list[_logging.LogRecord] = []
        if buffer_size is None:
            buffer_size = 100
        self._buffer_size: int = buffer_size
        if buffer_periodical_flush_timing is None:
            buffer_periodical_flush_timing = 5.0
        self._buffer_periodical_flush_timing: float = buffer_periodical_flush_timing
        if buffer_early_flush_level is None:
            buffer_early_flush_level = _logging.CRITICAL
        self._buffer_early_flush_level: int = buffer_early_flush_level
        self._buffer_timer_thread: _Optional[_threading.Thread] = None
        self._buffer_lock: _threading.Lock = _threading.Lock()
        self._stopper: _Optional[callable] = None

        # setup periodical flush
        if self._buffer_periodical_flush_timing:
            # clean exit event
            _atexit.register(self.close)

            # call at interval function
            def call_repeatedly(interval, func, *args):
                stopped = _threading.Event()

                # actual thread function
                def loop():
                    while not stopped.wait(interval):  # the first call is in `interval` secs
                        func(*args)

                timer_thread = _threading.Thread(name=f"{self.__class__.__name__}-{_counter()}", target=loop, daemon=True)
                timer_thread.start()
                return stopped.set, timer_thread

            # launch thread
            self._stopper, self._buffer_timer_thread = call_repeatedly(self._buffer_periodical_flush_timing, self.flush)

    def emit(self, record: _logging.LogRecord) -> None:
        with self._buffer_lock:
            self._buffer.append(record)

        if len(self._buffer) >= self._buffer_size or record.levelno >= self._buffer_early_flush_level:
            self.flush()

    def flush(self):
        if len(self._buffer) == 0:
            return

        with self._buffer_lock:
            formated_records = []
            for record in self._buffer:
                try:
                    formated_record = self.formatter.format(record)
                    formated_records.append(formated_record)
                except Exception:
                    self.handleError(record)
                if len(formated_records) == 0:
                    continue
            if len(formated_records) > 0:
                # create document
                document = self._document(timestamp=_local_now(),
                                          entries=formated_records,
                                          **self._document_kwargs)
                document.save()
            self.empty_buffer()

    def empty_buffer(self) -> None:
        """
        Empty the buffer list.

        :return: None
        """
        del self._buffer
        self._buffer = []

    def close(self) -> None:
        """
        Clean quit logging. Flush buffer. Stop the periodical thread if needed.

        :return: None
        """

        if self._stopper:
            self._stopper()
        self.flush()
        super().close()
