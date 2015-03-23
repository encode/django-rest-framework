#!/bin/bash
if [[ "$@" == "djangorestframework" ]]; then
  # Caching djangorestframework package would invalidate Travis cache on every build
  pip install "$@"
else
  # Try to install from cache, download and install if that fails
  pip install --no-index --find-links=$PIP_CACHE "$@"
  EXIT_STATUS=$?
  if [ $EXIT_STATUS -ne 0 ]; then
    pip install --download $PIP_CACHE "$@"
    pip install --no-index --find-links=$PIP_CACHE "$@"
  fi
fi
