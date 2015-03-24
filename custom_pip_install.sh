#!/bin/bash

while [[ $# > 1 ]]
do
requirement="$1"
  # Only requirements with "Django" in the name are being cached
  if [[ "$requirement" == *"Django"* ]]
  then
    # Try to install from cache
    pip install --no-index --find-links=$WHEEL_DIR "$requirement";
    EXIT_STATUS=$?
    # If that fails, try to make a wheel
    if [ $EXIT_STATUS -ne 0 ]
    then
      pip wheel --wheel-dir=$WHEEL_DIR "$requirement";
      EXIT_STATUS=$?
      # If that fails, install wheel and make wheel
      if [ $EXIT_STATUS -ne 0 ]
      then
          # Wheel version same as in requirements/requirements-packaging.txt
          pip install wheel==0.24.0;
          pip wheel --wheel-dir=$WHEEL_DIR "$requirement";
      fi
      # Install from cache
      pip install --no-index --find-links=$WHEEL_DIR "$requirement";
    fi
  else
      pip install "$requirement";
  fi
shift
done
