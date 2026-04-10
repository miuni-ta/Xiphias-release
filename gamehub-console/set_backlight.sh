#!/bin/bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <device> <raw_brightness>" >&2
  exit 2
fi

DEVICE="$1"
RAW_VALUE="$2"

if [[ ! "$DEVICE" =~ ^[A-Za-z0-9._:-]+$ ]]; then
  echo "invalid backlight device: $DEVICE" >&2
  exit 2
fi

if [[ ! "$RAW_VALUE" =~ ^[0-9]+$ ]]; then
  echo "invalid backlight value: $RAW_VALUE" >&2
  exit 2
fi

BACKLIGHT_DIR="/sys/class/backlight/${DEVICE}"
BRIGHTNESS_FILE="${BACKLIGHT_DIR}/brightness"
MAX_FILE="${BACKLIGHT_DIR}/max_brightness"

if [[ ! -f "$BRIGHTNESS_FILE" || ! -f "$MAX_FILE" ]]; then
  echo "backlight device not found: $DEVICE" >&2
  exit 1
fi

MAX_VALUE="$(cat "$MAX_FILE")"
if [[ ! "$MAX_VALUE" =~ ^[0-9]+$ ]]; then
  echo "invalid max brightness for $DEVICE" >&2
  exit 1
fi

if (( RAW_VALUE > MAX_VALUE )); then
  RAW_VALUE="$MAX_VALUE"
fi

printf '%s\n' "$RAW_VALUE" > "$BRIGHTNESS_FILE"
