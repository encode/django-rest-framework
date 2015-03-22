#!/bin/bash
pip install wheel==0.24.0
pip wheel --wheel-dir=${WHEEL_DIR} --find-links=${WHEEL_DIR} "$@"
pip install --no-index --find-links=${WHEEL_DIR} "$@"
