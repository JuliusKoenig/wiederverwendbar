from wiederverwendbar.logger import LoggerSingleton
from wiederverwendbar.logger import LoggerSettings


class TestSettings(LoggerSettings):
    qwe: str = "qwe"


test_settings = TestSettings(
    log_level="DEBUG",
    log_file=True,
    log_file_path="test.log"
)

if __name__ == '__main__':
    logger = LoggerSingleton(init=True, name="test", settings=test_settings)
    print()
