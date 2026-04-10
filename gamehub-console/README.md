# GameHub Console Setup

This folder is a ready-to-use starter package for a Raspberry Pi 5 handheld-style kiosk.

The canonical project workspace lives under `/home/pi/Xiphias/`.

The live kiosk tree now lives under `/home/pi/Xiphias/release/`. Runtime code, user-state, and kiosk assets should run from that `release/` subtree directly. The kiosk should not depend on duplicate `/home/pi/.config`, `/home/pi/.local`, `/home/pi/.icons`, or `/home/pi/.xinitrc` entry points.

It is built for:

- Raspberry Pi OS (64-bit) with desktop as the base image
- Raspberry Pi 5 with 4 GB RAM
- Chromium in fullscreen kiosk mode
- X11/Openbox instead of the default Wayland desktop
- SSH-based setup from another machine

What this package does:

- Boots straight into your website
- Hides the normal desktop
- Lets the gamepad move the mouse cursor
- Maps gamepad buttons to left click, right click, and `Ctrl+W` home/close-tab
- Keeps a static `Settings` label in the bottom HUD bar
- Shows a top HUD with clock, Wi-Fi, volume, Bluetooth, and battery when available

What is not generic on a Raspberry Pi:

- Battery percentage is not built into a Pi. You only get real battery status if your battery board exposes it through `upower` or a custom command.
- First-time secure Wi-Fi connection and first-time Bluetooth pairing are the hardest parts to make fully controller-only. This package gives you quick reconnect tools plus standard GUI helpers, but the cleanest first setup is still over SSH.

## Recommended Base OS

Use `Raspberry Pi OS (64-bit)` with desktop.

Do not start from `Raspberry Pi OS Lite` for this project unless you want extra work. Lite can be made to work, but you would still need to install the browser, X11, kiosk shell, keyboard, PolicyKit agent, and helper tools manually. For your use case, the desktop image is the better base even though the final system boots to kiosk instead of the normal desktop.

Your `Debian GNU/Linux 13 (trixie)` version string is normal for current Raspberry Pi OS releases because Raspberry Pi OS is based on Debian Trixie.

## Files

- `install_gamehub_console.sh`: one-shot installer
- `raspi-config-checklist.txt`: exact setup checklist
- `console.env`: main config values
- `start_kiosk_components.sh`: shared launcher for the HUD, controller daemon, and browser inside the active X session
- `launch_chromium.sh`: launches the website in kiosk mode
- `restart_kiosk.sh`: quickly restarts the kiosk HUD, controller daemon, and Chromium inside the current X session without rebooting the device
- `ota_git_update.sh`: pulls a staged release from GitHub and deploys only the managed kiosk files into the live Xiphias tree
- `gamepad_cursor.py`: gamepad-to-mouse bridge
- `hud_overlay.py`: top and bottom HUD bars
- `files/xinitrc`: X11 startup file
- `files/knf-kiosk.service`: systemd service for auto-start
- `files/90-xiphias-release-home`: systemd user-environment generator that keeps user-session config inside `release/`
- `files/openbox/autostart`: launches the HUD, controller, and browser

## Install Order

1. Flash `Raspberry Pi OS (64-bit)` with desktop using Raspberry Pi Imager.
2. In Imager advanced options, set hostname, username, password, Wi-Fi, locale, and enable SSH.
3. Boot the Pi once and SSH in.
4. Run `sudo raspi-config` and follow `raspi-config-checklist.txt`.
5. Run:

```bash
cd /home/pi/Xiphias/release/gamehub-console
bash install_gamehub_console.sh
```

6. Reboot:

```bash
sudo reboot
```

## First Network / Bluetooth Setup

For the first secure Wi-Fi connection and the first Bluetooth pairing, use one of these methods:

- Best during initial setup: configure Wi-Fi in Raspberry Pi Imager before first boot.
- Best after deployment: SSH into the Pi and use `nmcli` and `bluetoothctl`.
- Controller-only fallback: use the gamepad cursor plus the on-screen keyboard inside the hosted UI when available, or SSH in for advanced Wi-Fi and Bluetooth setup.

## Battery Support

If your battery board exposes a normal battery device to `upower`, the HUD will show battery automatically and switch to the charging icon only while `upower` reports `charging`.

If it does not, edit `console.env` and set `BATTERY_COMMAND` to a command that prints either a percentage number or JSON with `percent` plus optional `charging`, for example:

```bash
BATTERY_COMMAND=/usr/local/bin/read-battery-percent
```

This checkout now includes a Waveshare UPS HAT (B) reader and points `BATTERY_COMMAND` at it by default:

```bash
BATTERY_COMMAND="python3 /home/pi/Xiphias/release/gamehub-console/waveshare_ups_battery.py"
```

The bundled Waveshare reader reports both the battery percentage and charging state, so the HUD shows the bolt icon only while the pack is charging and falls back to the normal fill bar when it is not.

For that reader to work on a Raspberry Pi 5, make sure `I2C` is enabled in `raspi-config`. The script will auto-try the common INA219 addresses used by Waveshare UPS boards.

## Main Controls

- Left stick: move mouse
- `A`: left click
- `B` tap: right click
- `B` hold for 2 seconds: go home by closing the current tab
- `Y`: toggle on-screen keyboard
- `Start`: no HUD action in the current checkout
- `LB` / `RB`: scroll up / down
- D-pad up / down: scroll

## Git OTA Updates

For this project, the safer git-based OTA model is:

- keep `/home/pi/Xiphias` as the real git worktree
- keep the live kiosk tree under `/home/pi/Xiphias/release`
- pull a known branch, tag, or commit from GitHub
- back up the live kiosk state
- sync only the managed kiosk paths from `release/` into the live tree
- restart the kiosk

`/home/pi/Xiphias` is the real git worktree for `miuni-ta/Xiphias`, and `/home/pi/Xiphias/release` is the live kiosk tree. Treat the tracked `release/` subtree as both the deploy payload and the active runtime root on the device.

Set these in `console.env`:

```bash
OTA_REPO=miuni-ta/Xiphias-release
OTA_BRANCH=master
```

Then run:

```bash
bash /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh
```

If the OTA also changes `.xinitrc`, the systemd service, the cron file, or the sudoers file, run:

```bash
bash /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh --apply-system-files
```

The OTA script preserves the local `console.env`, keeps logs on the device, creates a rollback zip first by default, and only deploys the kiosk-managed paths instead of overwriting the whole home tree.

This public repository is the deploy mirror used by production devices. The maintenance/source repository remains separate.

## Safe Next Step

Use this as `v1`. Once the flow is stable on real hardware, the next step is to turn it into a custom image instead of a normal installed system.
