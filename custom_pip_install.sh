#!/bin/bash
if [[ "$@" == "djangorestframework" ]]; then
  # Caching djangorestframework package would invalidate Travis cache on every build
  pip install "$@"
else
  # Try to install from cache
  pip install --no-index --find-links=$WHEEL_DIR "$@"
  EXIT_STATUS=$?
  # If that fails, try to make a wheel
  if [ $EXIT_STATUS -ne 0 ]; then
    pip wheel --wheel-dir=$WHEEL_DIR "$@"
    EXIT_STATUS=$?
    # If that fails, install wheel and make wheel
    if [ $EXIT_STATUS -ne 0 ]; then
        pip install wheel==0.24.0
        pip wheel --wheel-dir=$WHEEL_DIR "$@"
    fi
    # Install from cache
    pip install --no-index --find-links=$WHEEL_DIR "$@"
  fi
fi
