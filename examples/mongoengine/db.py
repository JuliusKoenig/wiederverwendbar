from wiederverwendbar.logger import LoggerSingleton, LoggerSettings
from wiederverwendbar.mongoengine import MongoengineDbSingleton

LoggerSingleton(name="test", settings=LoggerSettings(log_level=LoggerSettings.LogLevels.DEBUG), init=True)

if __name__ == '__main__':
    MongoengineDbSingleton(init=True)
