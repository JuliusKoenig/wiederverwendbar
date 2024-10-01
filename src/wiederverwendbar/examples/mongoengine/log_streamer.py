import time

from wiederverwendbar.examples.mongoengine.logger import MyMongoengineLogDocument
from wiederverwendbar.mongoengine import MongoengineLogStreamer

if __name__ == '__main__':
    with MongoengineLogStreamer(MyMongoengineLogDocument) as streamer:
        while True:
            time.sleep(1)
