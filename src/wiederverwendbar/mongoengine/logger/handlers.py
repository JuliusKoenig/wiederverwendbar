import logging
import threading
from logging import NOTSET
from typing import Optional

from wiederverwendbar.functions.datetime import local_now
from wiederverwendbar.mongoengine.logger.documets import MongoengineLogDocument
from wiederverwendbar.mongoengine.logger.formatters import MongoengineLogFormatter


class MongoengineLogHandler(logging.Handler):
    def __init__(self,
                 level=NOTSET,
                 document: Optional[type[MongoengineLogDocument]] = None,
                 document_kwargs: Optional[dict] = None,
                 buffer_size: Optional[int] = None,
                 buffer_periodical_flush_timing: Optional[float] = None,
                 buffer_early_flush_level: Optional[int] = None):
        super().__init__(level=level)
        self.formatter: MongoengineLogFormatter = MongoengineLogFormatter()
        if document is None:
            document = MongoengineLogDocument
        self._document: type[MongoengineLogDocument] = document
        if document_kwargs is None:
            document_kwargs = {}
        self._document_kwargs: dict = document_kwargs
        self._buffer: list[logging.LogRecord] = []
        if buffer_size is None:
            buffer_size = 100
        self._buffer_size: int = buffer_size
        if buffer_periodical_flush_timing is None:
            buffer_periodical_flush_timing = 5.0
        self._buffer_periodical_flush_timing: float = buffer_periodical_flush_timing
        if buffer_early_flush_level is None:
            buffer_early_flush_level = logging.CRITICAL
        self._buffer_early_flush_level: int = buffer_early_flush_level
        self._buffer_timer_thread: Optional[threading.Thread] = None
        self._buffer_lock: threading.Lock = threading.Lock()
        self._timer_stopper: Optional[callable] = None

        # setup periodical flush
        if self._buffer_periodical_flush_timing:

            # clean exit event
            import atexit
            atexit.register(self.destroy)

            # call at interval function
            def call_repeatedly(interval, func, *args):
                stopped = threading.Event()

                # actual thread function
                def loop():
                    while not stopped.wait(interval):  # the first call is in `interval` secs
                        func(*args)

                timer_thread = threading.Thread(target=loop)
                timer_thread.daemon = True
                timer_thread.start()
                return stopped.set, timer_thread

            # launch thread
            self._timer_stopper, self._buffer_timer_thread = call_repeatedly(self._buffer_periodical_flush_timing, self.flush)

    def emit(self, record: logging.LogRecord) -> None:
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
            # create document
            document = self._document(timestamp=local_now(),
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

    def destroy(self) -> None:
        """
        Clean quit logging. Flush buffer. Stop the periodical thread if needed.

        :return: None
        """
        if self._timer_stopper:
            self._timer_stopper()
        self.flush()
        self.close()
