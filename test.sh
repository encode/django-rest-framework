#!/usr/bin/env bash
set -uo pipefail

OUTPUT_PATH=""
if [ "${1:-}" = "--output_path" ]; then
  OUTPUT_PATH="$2"
  shift 2
fi

MODE="${1:-new}"
STATUS=0

case "$MODE" in
  base)
    # Run existing DRF template tests to ensure no regression
    python runtests.py tests.test_templates --junitxml="${OUTPUT_PATH:-/tmp/base.xml}" || STATUS=$?
    ;;
  new)
    # Run the new Jinja2 support challenge test
    python runtests.py tests.test_jinja2_templates --junitxml="${OUTPUT_PATH:-/tmp/new.xml}" || STATUS=$?
    ;;
  *)
    echo "unknown mode: $MODE (expected base or new)" >&2
    exit 2
    ;;
esac

exit "$STATUS"