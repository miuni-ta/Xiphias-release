# Xiphias Changes

This is the required high-level development changelog for Xiphias.
Update this file whenever behavior, deployment, image-building, OTA, or kiosk UX changes.

Detailed historical kiosk notes before this file existed still live in `timestamp-console.md`.

## 2026-07-15

- Added a browser game-mode gate so hosted HTML games such as MakeCode Arcade receive USB and GPIO controller input through Chromium's Gamepad API without Xiphias also translating those presses into mouse clicks, scrolling, OSK toggles, home actions, or the `Start` Settings shortcut.
- Changed the Settings `Check for Updates` version display to the alpha label format `Alpha v1.0.0` and added a tracked version-bump hook/script so future commits can increment the patch number automatically.
- Changed the GPIO virtual controller to use a Chromium-standard Xbox-compatible browser identity and emit explicit D-pad button events, preventing MakeCode Arcade and the hosted portal from seeing raw Linux button indexes such as L2 as `back` or Select as reset.
- Sped up Settings Bluetooth reconnects for already-paired devices by trying direct `bluetoothctl connect` first, while preserving the older scan plus session-setup fallback when a device rejects the bare reconnect.
- Kept Bluetooth failure messages visible in Settings for 5 seconds so raw BlueZ errors such as `org.bluez.Error.Failed` can be read during connection troubleshooting.
- Added stale-pairing recovery for Bluetooth `br-connection-key-missing` failures by removing the broken local bond and trying one fresh pair/connect sequence.
- Capped Settings Bluetooth connect attempts at about 8 seconds before falling through to the next fallback path.
- Added explicit Settings Bluetooth action rows for Connect/Pair, Disconnect, Forget device, and Forget all saved devices.
- Reworked Settings Wi-Fi and Bluetooth details so network/device actions open from D-pad right in a nested action panel instead of appearing directly in the main list.

## 2026-07-09

- Added a Settings `Button Tester` row after `Bluetooth`, opening a canvas-drawn controller diagram that listens to USB and GPIO gamepads, highlights live button input, suppresses normal Settings actions while testing, and exits on held `Start`.

## 2026-05-20

- Added native external GPIO gamepad support for the Xiphias handheld, exposing the 14-button BCM GPIO wiring as a virtual `Xiphias GPIO Gamepad` evdev device.
- Added installer, image-builder, and OTA system-file hooks for the GPIO gamepad service and `uinput` module loading.
- Updated controller handling so the GPIO D-pad moves the cursor without also scrolling the hosted page, while still navigating the runtime Settings overlay through HAT events.
- Tightened the GPIO bridge to present as a USB-style generic controller, including udev joystick/gamepad tagging and L2/R2 trigger-axis events for better Chromium and OS compatibility.
- Fixed GPIO controller detection so Xiphias prefers the `Xiphias GPIO Gamepad` device and ignores unrelated absolute-axis input devices, and added a Pi-side diagnostic script for service, uinput, dependency, udev, and journal checks.
- Added `joydev` loading for the GPIO virtual controller so Chromium/browser gamepad paths can see a `/dev/input/js*` joystick node, and expanded the GPIO diagnostic script to print configured BCM pins plus live pressed/released pin states.

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
