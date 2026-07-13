#!/usr/bin/env bash
set -euo pipefail

: "${SERVICEFABRIC_HOME:=$(mktemp -d)/servicefabric}"
export SERVICEFABRIC_HOME

servicefabric init
servicefabric apps install examples/text-utility
servicefabric apps build text-utility
servicefabric apps start text-utility
servicefabric apps status text-utility
servicefabric apps resources text-utility
servicefabric tools list
servicefabric tools describe text.count_words
servicefabric call text.count_words \
  --input '{"text":"ServiceFabric hosts applications and capabilities."}'
servicefabric apps stop text-utility

if servicefabric call text.count_words --input '{"text":"must not execute"}'; then
  echo "stopped capability unexpectedly executed" >&2
  exit 1
fi
