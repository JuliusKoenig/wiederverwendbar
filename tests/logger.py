import logging

from wiederverwendbar.logger import LoggerSingleton
from wiederverwendbar.logger import LoggerSettings

import uvicorn
from fastapi import FastAPI


class TestSettings(LoggerSettings):
    qwe: str = "qwe"


test_settings = TestSettings(
    log_level="DEBUG",
    log_file=True,
    log_file_path="test.log"
)

if __name__ == '__main__':
    logger = LoggerSingleton(init=True, name="test", settings=test_settings, ignored_loggers_like=["uvicorn"])

    sub_logger = logging.getLogger("sub")

    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")

    sub_logger.debug("debug")
    sub_logger.info("info")
    sub_logger.warning("warning")
    sub_logger.error("error")
    sub_logger.critical("critical")

    app = FastAPI()

    uvicorn.run(app, host="0.0.0.0", port=8000)

    print()
