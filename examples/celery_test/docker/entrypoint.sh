#!/usr/bin/env bash

MODE=$1
APP_TITLE=$(python -c "from $MODULE_NAME import __title__; print(__title__)")
APP_DESCRIPTION=$(python -c "from $MODULE_NAME import __description__; print(__description__)")
APP_VERSION=$(python -c "from $MODULE_NAME import __version__; print(__version__)")
APP_AUTHOR=$(python -c "from $MODULE_NAME import __author__; print(__author__)")
APP_AUTHOR_EMAIL=$(python -c "from $MODULE_NAME import __author_email__; print(__author_email__)")
APP_LICENSE=$(python -c "from $MODULE_NAME import __license__; print(__license__)")
APP_LICENSE_URL=$(python -c "from $MODULE_NAME import __license_url__; print(__license_url__)")
APP_TERMS_OF_SERVICE=$(python -c "from $MODULE_NAME import __terms_of_service__; print(__terms_of_service__)")

# if no mode is provided, print usage and loop forever
if [ -z "$MODE" ]; then
  echo "No mode provided. Looping forever..."
  # loop forever
  while true; do
    sleep 1
  done
  exit 0
fi

function usage() {
  echo "Usage: $0 <mode>"
  echo "Modes:"
  echo "  worker - Start the Celery worker"
  echo "  beat   - Start the Celery beat"
  echo "If no mode is provided, the script will loop forever."
  exit 1
}

function header() {
  echo "Starting $APP_TITLE - $MODE ..."
  echo "----------------------------------------------------------------"
  echo "Version: $APP_VERSION"
  echo "Description: $APP_DESCRIPTION"
  echo "Author: $APP_AUTHOR"
  echo "Author Email: $APP_AUTHOR_EMAIL"
  echo "License: $APP_LICENSE"
  echo "License URL: $APP_LICENSE_URL"
  echo "Terms of Service: $APP_TERMS_OF_SERVICE"
  echo "----------------------------------------------------------------"
}

function footer() {
  echo "Stopped $APP_TITLE - $MODE successfully."
}

# if mode is worker, start the worker
if [ "$MODE" = "worker" ]; then
  # print the header
  header

  # ensure that the worker user and group exist have permissions
  chown -R "$WORKER_UID:$WORKER_GID" /var/run/celery/

  # build the command
  CMD="celery worker --loglevel=$WORKER_LOG_LEVEL --uid=$WORKER_UID --gid=$WORKER_GID --pidfile=$WORKER_PID_FILE"

  # add log file enabled
  if [ "$WORKER_LOG_FILE_ENABLED" = "true" ]; then
    CMD="$CMD --logfile=$WORKER_LOG_FILE"
  fi

  # run the command
  eval $CMD
  EXIT_CODE=$?

  # print the footer
  footer

  # exit with the exit code of the command
  exit $EXIT_CODE
elif [ "$MODE" = "beat" ]; then
  # print the header
  header

  # ensure that the beat user and group exist have permissions
  chown -R "$BEAT_UID:$BEAT_GID" /var/run/celery/

  # build the command
  CMD="celery beat --loglevel=$BEAT_LOG_LEVEL --uid=$BEAT_UID --gid=$BEAT_GID --pidfile=$BEAT_PID_FILE"

  # add log file enabled
  if [ "$BEAT_LOG_FILE_ENABLED" = "true" ]; then
    CMD="$CMD --logfile=$BEAT_LOG_FILE"
  fi

  # run the command
  eval $CMD
  EXIT_CODE=$?

  # print the footer
  footer

  # exit with the exit code of the command
  exit $EXIT_CODE
else
  echo "Unknown mode: $MODE"
  usage
fi


