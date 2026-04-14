# Xiphias Changes

This is the required high-level development changelog for Xiphias.
Update this file whenever behavior, deployment, image-building, OTA, or kiosk UX changes.

Detailed historical kiosk notes before this file existed still live in `timestamp-console.md`.

## 2026-04-14

- Added this `xiphias-changes.md` file as the canonical high-level project change log.
- Fixed Bluetooth pairing reliability by replacing the interactive `bluetoothctl` PTY/script flow with deterministic sequential command execution and by explicitly enabling `pairable` plus `discoverable` before pairing attempts.
- Added update-note bullet points to the Settings `Check for Updates` confirm dropdown, sourced from OTA metadata generated from recent change summaries.
- Fixed the OTA restart handoff so successful installs let `ota_git_update.sh` own the kiosk restart instead of relying on the old HUD process after self-update.
- Rebuilt and re-verified `xiphias.img` so the current image includes the newer battery detection, OTA, and first-boot fixes.
- Improved first-boot image behavior with automatic hostname finalization, default-password setup, public-safe OTA config, and cleanup of machine-specific state in built images.
- Fixed battery detection, brightness handling, touch slider interaction, settings highlight rounding, and kiosk restart environment consistency.

## 2026-04-10

- Added automated publishing from private `Xiphias` to public `Xiphias-release` through GitHub Actions.
- Added a reproducible `xiphias.img` image builder and documented the image-build workflow.
- Created the clean public release repo flow so production devices can update from `Xiphias-release` without shipping a private maintenance credential.

## 2026-04-09

- Split the project into a private maintenance repo (`Xiphias`) and a public production release repo (`Xiphias-release`).
- Moved the live kiosk runtime to `/home/pi/Xiphias/release` and cleaned the duplicate home-root runtime layout.
- Added the Git-based OTA update path, update checking in the Settings menu, release staging sync, and restart handling for deployed updates.
- Hardened OTA against dirty local worktrees, shallow clones, and repo-only upstream changes that should not force a kiosk restart.

## 2026-04-07

- Promoted `/home/pi/Xiphias` as the canonical kiosk workspace and updated service, cron, sudoers, and runtime paths to match.
- Removed the older `/home/pi/release` layout after the live kiosk was confirmed healthy from the Xiphias-root path.
- Standardized backup generation, installed system files, and Openbox/X startup around the Xiphias-root structure.

## 2026-04-06

- Shaped the early kiosk UX around boot splash behavior, settings overlay work, shared UI audio cues, and the console-style Onboard keyboard direction.
- See `timestamp-console.md` for the detailed dated entries from this earlier development phase.
