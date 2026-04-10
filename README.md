# Xiphias Release

This public repository contains the deploy payload for the Xiphias handheld kiosk.

The repository root mirrors the content that should live at `/home/pi/Xiphias/release` on a device. It is intended for production OTA updates and release distribution, not day-to-day maintenance work.

The private maintenance/source repository remains separate. Production devices should update from this public release repository.

## Repo Layout

- `.config/`
- `.icons/`
- `.local/`
- `.xinitrc`
- `gamehub-console/`
- `version.txt`

## OTA

Production devices should use:

```bash
OTA_REPO=miuni-ta/Xiphias-release
OTA_BRANCH=master
```

No `OTA_TOKEN` is required for public-read updates.
