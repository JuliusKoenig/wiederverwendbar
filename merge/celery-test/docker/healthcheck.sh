#!/usr/bin/env bash

MODE=$1

function usage() {
  echo "Usage: $0 <mode>"
  echo "Modes:"
  echo "  worker - Start the Celery worker"
  echo "  beat   - Start the Celery beat"
  echo "If no mode is provided, the script will loop forever."
  exit 1
}

PID_FILE=""

# get the pid file
if [ "$MODE" = "worker" ]; then
  PID_FILE="$WORKER_PID_FILE"
elif [ "$MODE" = "beat" ]; then
  PID_FILE="$BEAT_PID_FILE"
else
  echo "Unknown mode: $MODE"
  usage
fi

# check if the pid file exists
if [ -f "$PID_FILE" ]; then
  # read the pid from the file
  PID=$(cat "$PID_FILE")

  # check if the process is running
  if ps -p $PID > /dev/null; then
    echo "Process with PID $PID is running."
    exit 0
  else
    echo "Process with PID $PID is not running."
    exit 1
  fi
else
  echo "PID file $PID_FILE does not exist."
  exit 1
fi
