#!/bin/bash
export XCURSOR_THEME="${XCURSOR_THEME:-GameHubCursor}"
export XCURSOR_SIZE="${XCURSOR_SIZE:-32}"
xset -dpms
xset s off
xset s noblank
exec openbox-session
