#!/usr/bin/env bash
set -euo pipefail

# Ensure a clean temporary directory for the baseline
export SERVICEFABRIC_HOME="$(mktemp -d)"

echo "Using temporary SERVICEFABRIC_HOME: ${SERVICEFABRIC_HOME}"

# Always clean up the process on exit
cleanup() {
  echo "Cleaning up..."
  servicefabric apps stop text-utility >/dev/null 2>&1 || true
  rm -rf "${SERVICEFABRIC_HOME}"
}
trap cleanup EXIT

echo "1. Initializing workspace..."
servicefabric init

echo "2. Installing examples/text-utility..."
servicefabric apps install examples/text-utility

echo "3. Building text-utility..."
servicefabric apps build text-utility

echo "4. Starting text-utility..."
servicefabric apps start text-utility

echo "5. Checking status..."
servicefabric apps status text-utility --json

echo "6. Checking resources..."
servicefabric apps resources text-utility --json

echo "7. Stopping text-utility..."
servicefabric apps stop text-utility

echo "8. Checking status after stop..."
servicefabric apps status text-utility --json

echo "Baseline journey completed successfully!"
