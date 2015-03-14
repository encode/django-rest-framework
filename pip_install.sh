#!/bin/bash

echo "$@"
pip wheel "$@"
pip install --upgrade "$@"
