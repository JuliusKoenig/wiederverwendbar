FROM python:3.13-bookworm
LABEL author="Julius Koenig"
LABEL author_email="info@bastelquartier.de"

# upgrade pip
RUN pip install --upgrade pip

# copy source files
COPY ../src /app/src
COPY ../tests /app/tests
COPY ../pyproject.toml /app/pyproject.toml
COPY ../README.md /app/README.md
COPY ../LICENSE /app/LICENSE

# install project requirements
RUN pip install -e /app

# copy celery.py script
COPY ./docker/celery.py /usr/local/bin/celery

# copy healthcheck.sh script
COPY ./docker/healthcheck.sh /healthcheck.sh

# copy entrypoint.sh script
COPY ./docker/entrypoint.sh /entrypoint.sh

# create directories for logs and pid files
RUN mkdir -p /var/log/celery
RUN mkdir -p /var/run/celery

# set default environment
ENV MODULE_NAME=celery_test
ENV WORKER_LOG_LEVEL=WARNING
ENV WORKER_LOG_FILE_ENABLED=true
ENV WORKER_LOG_FILE=/var/log/celery/worker.log
ENV WORKER_PID_FILE=/var/run/celery/worker.pid
ENV WORKER_UID=nobody
ENV WORKER_GID=nogroup
ENV BEAT_LOG_LEVEL=WARNING
ENV BEAT_LOG_FILE_ENABLED=true
ENV BEAT_LOG_FILE=/var/log/celery/beat.log
ENV BEAT_PID_FILE=/var/run/celery/beat.pid
ENV BEAT_UID=nobody
ENV BEAT_GID=nogroup
ENV DB_HOST=localhost
ENV DB_PORT=3306
ENV DB_USERNAME=admin
ENV DB_PASSWORD=password
ENV DB_DATABASE_NAME=test
ENV DB_ADMIN_PORT=8001
ENV BROKER_HOST=localhost
ENV BROKER_PORT=5672
ENV BROKER_USERNAME=admin
ENV BROKER_PASSWORD=password

ENTRYPOINT ["/entrypoint.sh"]