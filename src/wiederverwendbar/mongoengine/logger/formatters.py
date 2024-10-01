import logging


class MongoengineLogFormatter(logging.Formatter):
    DEFAULT_PROPERTIES = logging.LogRecord('', 0, '', 0, '', (), (None, None, None), '').__dict__.keys()

    def format(self, record) -> dict:
        """
        Formats LogRecord into python dictionary.

        :param record: LogRecord instance.
        :return: dict
        """

        # standard entry
        entry = {
            'timestamp': record.created,
            'level': record.levelname,
            'thread': record.thread,
            'thread_name': record.threadName,
            'message': record.getMessage(),
            'logger_name': record.name,
            'file_name': record.pathname,
            'module': record.module,
            'method': record.funcName,
            'line_number': record.lineno
        }

        # add exception information if present
        if record.exc_info is not None:
            entry.update({
                'exception': {
                    'message': str(record.exc_info[1]),
                    'code': 0,
                    'stack_trace': self.formatException(record.exc_info)
                }
            })

        # add extra information
        if len(self.DEFAULT_PROPERTIES) != len(record.__dict__):
            contextual_extra = set(record.__dict__).difference(
                set(self.DEFAULT_PROPERTIES))
            if contextual_extra:
                for key in contextual_extra:
                    entry[key] = record.__dict__[key]

        return entry
