# Timestamp Console Log

Use this file to keep a dated record of kiosk changes made on the Raspberry Pi. Add a new entry for every behavior, configuration, startup, display, input, or UI change that affects the kiosk runtime.

## Entry Template

```md
## YYYY-MM-DD HH:MM:SS TZ
- Summary: short description of the kiosk change.
- Files: /absolute/or/repo-relative/path list.
- Verification: commands run or behavior checked on-device.
```

## 2026-04-07 11:06:41 +0800
- Summary: Moved the splash jingle into a shared helper and added a new `Splash` row to the live Settings overlay so pressing `A` there plays the current splashscreen audio on demand for testing.
- Files: `splash_audio.py`, `boot_splash.py`, `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260407-110332.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260407-110332.md` from the pre-edit `AGENTS.md`, ran `python3 -m py_compile /home/pi/gamehub-console/boot_splash.py /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/splash_audio.py`, ran a `DISPLAY=:0 PYTHONPATH=/home/pi/gamehub-console python3` Tk sanity check confirming `QuickMenuOverlay` now exposes `['volume', 'wifi', 'bt', 'brightness', 'splash', 'restart', 'shutdown']` and that `execute_item('splash')` triggers one jingle-play call plus the `Playing splash jingle...` toast path, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed the live session came back with `unclutter -idle 0 -root`, `python3 /home/pi/gamehub-console/hud_overlay.py`, `python3 /home/pi/gamehub-console/gamepad_cursor.py`, and `/bin/bash /home/pi/gamehub-console/launch_chromium.sh`; final audible verification of the new Settings-row trigger still requires using the live overlay on-device.

## 2026-04-07 10:57:07 +0800
- Summary: Added a short synthesized splash-screen jingle to `boot_splash.py` so both the fallback splash and the Plymouth handoff overlay now play one compact 6/4 startup phrase with slurred low opening tones, a half-beat rest, and an accented closing triplet.
- Files: `boot_splash.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260407-105707.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260407-105707.md` from the pre-edit `AGENTS.md`, ran `python3 -m py_compile /home/pi/gamehub-console/boot_splash.py`, and ran `PYTHONPATH=/home/pi/gamehub-console python3` sanity checks confirming `SplashJinglePlayer` builds a non-empty PCM phrase on the live `pacat` backend at `44100 Hz` stereo with duration `0.972` seconds; final audible verification of the boot-path jingle still requires a cold boot or an explicitly forced splash run on-device.

## 2026-04-07 10:20:03 +0800
- Summary: Restored a real X-session boot handoff so the Plymouth logo now stays onscreen until Chromium has a visible kiosk window, shortened the Chromium launch delay, and added a branded loader to `kiosk-wrapper.html` so the browser shell appears immediately instead of sitting on a blank black surface while the hosted page loads.
- Files: `boot_splash.py`, `start_kiosk_components.sh`, `launch_chromium.sh`, `kiosk-wrapper.html`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260407-102003.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260407-102003.md` from the pre-edit `AGENTS.md`, ran `python3 -m py_compile /home/pi/gamehub-console/boot_splash.py`, ran `bash -n /home/pi/gamehub-console/start_kiosk_components.sh /home/pi/gamehub-console/restart_kiosk.sh /home/pi/gamehub-console/launch_chromium.sh`, ran `bash /home/pi/gamehub-console/restart_kiosk.sh`, confirmed the live session came back with `unclutter -idle 0 -root`, `python3 /home/pi/gamehub-console/hud_overlay.py`, `python3 /home/pi/gamehub-console/gamepad_cursor.py`, and `/bin/bash /home/pi/gamehub-console/launch_chromium.sh`, confirmed `/tmp/gamehub-boot-ready` is created by the Chromium launch path, and queried the live wrapper through the Chromium DevTools endpoint to confirm `loaderExists: true`, `loaderHidden: true`, `fallbackVisible: false`, and `frameSrc: "https://handheld.knfstudios.com/?mode=handheld"` after the iframe finished loading; full cold-boot visual confirmation of the Plymouth-to-X handoff still requires an on-device reboot.

## 2026-04-06 11:04:29 +08
- Summary: Replaced the larger Wi-Fi-only connection toast with a smaller shared connected popup and now show it for both successful Wi-Fi joins and Bluetooth device connections.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-110429.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260406-110429.md` from the pre-edit `AGENTS.md`, ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, and checked the updated toast wiring in `hud_overlay.py` to confirm the shared `connection_toast` path is used by both `handle_wifi_connected()` and `handle_bluetooth_connected()`; live on-device visual verification of the smaller popup is still recommended.

## 2026-04-06 11:00:29 +08
- Summary: Added synthesized settings-overlay audio cues in `hud_overlay.py` for opening and closing Settings, focus navigation, slider adjustments, manual Wi-Fi/Bluetooth refresh, successful device connections, and the Restart Kiosk / Shutdown confirmation flows.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-110029.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260406-110029.md` from the pre-edit `AGENTS.md`, ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, and ran a `PYTHONPATH=/home/pi/gamehub-console python3` import check confirming `UiSoundPlayer` detected the local `paplay` backend and generated non-empty PCM buffers for the open, close, scroll, slider, refresh, confirm, restart, and shutdown sound patterns; live on-device audible verification in the running Settings overlay is still recommended.

## 2026-04-03 18:17:17 +08
- Summary: Disabled double-click text selection and selection highlight across the kiosk browser for non-editable page content by adding a wrapper-level no-selection style and a DevTools-injected selection lock that still preserves normal input and textarea editing.
- Files: `kiosk-wrapper.html`, `gamepad_cursor.py`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, restarted the live kiosk with `bash /home/pi/gamehub-console/restart_kiosk.sh`, confirmed Chromium returned on the local DevTools endpoint, and evaluated `window.__gamehubSelectionLockInstalled===true` through `gamepad_cursor.py` against both the wrapper page and hosted iframe targets.

## 2026-04-02 14:36:01 +08
- Summary: Normalized the `Caps` and `Enter` icon render size to match the `Backspace` icon by adding explicit image-box margins to the taller side keys while leaving their large hit areas intact.
- Files: `gamepad_keyboard.onboard`, `timestamp-console.md`.
- Verification: Parsed `gamepad_keyboard.onboard` and confirmed `CAPS` now uses `label_margin="23,20.5"` and `RTRN` uses `label_margin="28,20.5"` while `BKSP` remains the baseline icon key with no extra margin override.

## 2026-04-02 14:31:15 +08
- Summary: Reduced the remaining alphanumeric OSK label size again by increasing their per-key label margins while keeping `Caps` and `Enter` icon-only.
- Files: `gamepad_keyboard.onboard`, `timestamp-console.md`.
- Verification: Parsed the updated `gamepad_keyboard.onboard` XML and verified the new `label_margin="5,11"` settings are present on the alphanumeric keys before reloading the kiosk components.

## 2026-04-02 14:26:38 +08
- Summary: Swapped the OSK `Enter` and `Caps` keys from text labels to the requested icon assets, linked those icon filenames into Onboard's layout-local image lookup path, retinted the OSK icon set to white for contrast on the dark keys, and reduced the remaining alphanumeric label size slightly with safer per-key margins.
- Files: `gamepad_keyboard.onboard`, `assets/icons/osk_icons/osk_backspace.png`, `assets/icons/osk_icons/osk_shift.png`, `assets/icons/osk_icons/osk_enter.png`, `assets/icons/osk_icons/osk_caps.png`, `images/osk_caps.png`, `images/osk_enter.png`, `/home/pi/.local/share/onboard/layouts/images/osk_caps.png`, `/home/pi/.local/share/onboard/layouts/images/osk_enter.png`, `timestamp-console.md`.
- Verification: Parsed `gamepad_keyboard.onboard`, confirmed the new icon symlinks exist in both layout image lookup paths, inspected the updated PNG assets directly, and prepared the live kiosk restart; direct `onboard` CLI preview in the shell context exited immediately without stderr output, so the runtime reload path remains the authoritative live check.

## 2026-04-02 14:14:29 +08
- Summary: Fixed the OSK regression where the letter and number labels disappeared by removing the overly aggressive label margins from the alphanumeric keys while keeping the stretched `Caps` and `Enter` keys and the compact `800x180` layout.
- Files: `gamepad_keyboard.onboard`, `timestamp-console.md`.
- Verification: Parsed the updated `gamepad_keyboard.onboard` XML and launched `Onboard` on `DISPLAY=:0` with `--size=800x180` to confirm the repaired layout still starts cleanly.

## 2026-04-02 14:07:56 +08
- Summary: Tightened the compact `800x180` Onboard layout again by shrinking visible text toward the requested `9px` target via larger label margins, making the spacebar share the same fill/stroke colors as the main letter keys, and stretching the `Caps` and `Enter` keys vertically so they span the row beneath them.
- Files: `gamepad_keyboard.onboard`, `gamepad_keyboard.svg`, `gamepad_dark.colors`, `timestamp-console.md`.
- Verification: Parsed the updated layout/color XML, confirmed the stretched `CAPS` and `RTRN` rects exist at `height=75` in the SVG, launched `Onboard` on `DISPLAY=:0` with `--size=800x180` to confirm the revised layout loads successfully, and synced the updated `gamepad_dark.colors` into `/home/pi/.local/share/onboard/themes/`.

## 2026-04-02 13:17:11 +08
- Summary: Switched the live Onboard keyboard to a fixed `800x180` compact layout, removed the left/right arrow keys from the OSK entirely, tightened the row geometry to the requested compact dark-console proportions, and regrouped labels so small-text keys such as `Caps` and `Enter` render smaller than the main alpha keys.
- Files: `gamepad_cursor.py`, `gamepad_keyboard.onboard`, `gamepad_keyboard.svg`, `gamepad_dark.theme`, `gamepad_dark.colors`, `timestamp-console.md`.
- Verification: Parsed the updated layout/theme XML, confirmed all remaining layout keys still map to SVG rects, synced the updated theme files into `/home/pi/.local/share/onboard/themes/`, and prepared a live `Onboard` preview plus kiosk-component restart against the fixed `800x180` size.

## 2026-04-02 13:09:35 +08
- Summary: Reworked the live Onboard keyboard to match the requested flat SteamOS/Switch-style dark spec by expanding the runtime keyboard height to fit five `44px` rows with `5px` gutters and `10px` outer padding, redrawing the SVG hitboxes around that rhythm, and replacing the previous accent-heavy theme with a neutral grayscale palette based on `#2C2C2C`, `#3D3D3D`, and `#262626`.
- Files: `gamepad_cursor.py`, `gamepad_keyboard.svg`, `gamepad_dark.theme`, `gamepad_dark.colors`, `timestamp-console.md`.
- Verification: Parsed the updated OSK XML/theme files with `xml.etree.ElementTree`, synced `gamepad_dark.theme` and `gamepad_dark.colors` into `/home/pi/.local/share/onboard/themes/`, and prepared a kiosk component restart so the live `Onboard` launch path picks up the new `260px` geometry.

## 2026-04-02 12:45:10 +08
- Summary: Restyled the live Onboard keyboard toward a cleaner SteamOS/Switch-style console layout by removing the Tab and Hide keys, moving both Shift keys beside the spacebar, switching Shift and Backspace to icon-only keys from `assets/icons/osk_icons`, and tuning the dark theme/colors so label sizing reads more evenly across the remaining keys.
- Files: `gamepad_keyboard.onboard`, `gamepad_keyboard.svg`, `gamepad_dark.theme`, `gamepad_dark.colors`, `images/osk_backspace.png`, `images/osk_shift.png`, `timestamp-console.md`.
- Verification: Parsed `gamepad_keyboard.onboard`, `gamepad_keyboard.svg`, `gamepad_dark.theme`, and `gamepad_dark.colors` with `xml.etree.ElementTree`, confirmed every layout key has matching SVG geometry, linked the new icon filenames into the layout-local `images/` lookup path, synced the updated theme/colors into `/home/pi/.local/share/onboard/themes/`, and launched `Onboard` on `DISPLAY=:0` with the updated layout/theme to confirm it starts without emitting layout or image-resolution errors.

## 2026-04-02 10:06:35 +08
- Summary: Updated the live Bluetooth settings list to sort named devices ahead of MAC-style placeholder entries and to render unnamed devices as `Unknown <Type>` labels such as `Unknown Controller` instead of exposing raw addresses.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-100635.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260402-100635.md` from the pre-edit `AGENTS.md`, ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, ran `bash /home/pi/gamehub-console/restart_kiosk.sh`, and confirmed fresh `hud_overlay.py`, `launch_chromium.sh`, and Chromium processes with `pgrep -af`.

## 2026-04-02 09:41:28 +08
- Summary: Switched the rollback-backup naming convention to timestamped `console_backup_YYYYMMDD_HHMMSS.zip` archives, documented that rule in `AGENTS.md`, and created `/home/pi/backup/console_backup_20260402_094128.zip`.
- Files: `backup_rollback_zip.sh`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-093958.md`, `/home/pi/backup/console_backup_20260402_094128.zip`.
- Verification: Created `/home/pi/backup/AGENTS-20260402-093958.md` from the pre-edit `AGENTS.md`, ran `bash -n /home/pi/gamehub-console/backup_rollback_zip.sh`, ran `bash /home/pi/gamehub-console/backup_rollback_zip.sh`, confirmed `/home/pi/backup/console_backup_20260402_094128.zip` exists, and checked with Python `zipfile` that the archive contains kiosk paths with no `.codex` entries and no `gamehub-console/logs/*` files.

## 2026-04-02 09:32:29 +08
- Summary: Replaced the plain-text dropdown control hints inside the live Settings overlay with inline Xbox prompt icons, including D-pad hints for the live volume and brightness panels plus A-button hints for Bluetooth selection and destructive confirmation panels.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-093229.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260402-093229.md` from the pre-edit `AGENTS.md` and ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`; live visual verification follows from restarting the kiosk overlay.

## 2026-04-02 09:28:54 +08
- Summary: Rebalanced the live Settings overlay WiFi/Bluetooth dropdown layout so the detail panel uses matched outer margins and the inner list-item borders sit slightly inset from the container border for cleaner padding and spacing.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-092625.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260402-092625.md` from the pre-edit `AGENTS.md`, ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, and ran `bash /home/pi/gamehub-console/restart_kiosk.sh` to reload the live kiosk overlay.

## 2026-04-01 18:02:13 +08
- Summary: Constrained controller-driven cursor movement to the Onboard keyboard rectangle whenever the OSK is open, and snapped the pointer into that region as the keyboard appears so controller navigation cannot drift back into the hosted page behind the keyboard.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260401-180213.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260401-180213.md` from the pre-edit `AGENTS.md` before patching the repo files, ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py /home/pi/gamehub-console/hud_overlay.py`, ran `bash /home/pi/gamehub-console/restart_kiosk.sh`, confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, `launch_chromium.sh`, and Chromium processes with `pgrep -af`, and ran a Python import check against the live OSK state to confirm `keyboard_is_open()` is `True`, `keyboard_cursor_bounds()` returns `(0, 799, 266, 455)`, and controller clamp calls force out-of-range positions back into that rectangle.

## 2026-04-01 17:58:44 +08
- Summary: Restored cursor hiding inside the live Settings overlay by making the HUD cursor resolver honor the existing menu-visible hide flag even on touchscreen systems, while keeping the browser-side touchscreen cursor behavior unchanged outside the menu.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260401-175844.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260401-175844.md` from the pre-edit `AGENTS.md` before patching the repo files; live verification follows from `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py` and a kiosk restart.

## 2026-04-01 17:34:59 +08
- Summary: Updated the rollback backup path so `backup_rollback_zip.sh` now writes the latest zip into `/home/pi/backup`, aligned `AGENTS.md` with that backup-folder location, and added a rule to place a dated backup copy of `AGENTS.md` in `/home/pi/backup` before editing it.
- Files: `backup_rollback_zip.sh`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260401-173459.md`.
- Verification: Created `/home/pi/backup/AGENTS-20260401-173459.md` from the pre-edit `AGENTS.md` before patching the repo files, ran `bash -n /home/pi/gamehub-console/backup_rollback_zip.sh`, ran `bash /home/pi/gamehub-console/backup_rollback_zip.sh`, verified `/home/pi/backup/kiosk-backup-latest.zip` now exists with a fresh `2026-04-01 17:37:24 +08` modification time, and checked with Python `zipfile` that the archive contains kiosk paths only with no `.codex` entries and no `gamehub-console/logs/*` files.

## 2026-04-01 17:33:04 +08
- Summary: Prevented the runtime `Onboard` keyboard from overlapping the live Settings overlay by suppressing the OSK whenever the shared Settings/Quick Menu state is active, hiding any already-open keyboard immediately, and blocking keyboard reopen attempts until the overlay closes.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py /home/pi/gamehub-console/hud_overlay.py`, ran `bash /home/pi/gamehub-console/restart_kiosk.sh`, confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium processes in the relaunched kiosk session, and briefly toggled the shared `/tmp/gamehub-quick-menu-active` flag to exercise the new OSK-suppression path; full on-device verification of opening Settings while the OSK is visible is still recommended.

## 2026-04-01 17:30:08 +08
- Summary: Re-enabled a standard visible touchscreen cursor in the kiosk by skipping `unclutter` on touch devices, removing the wrapper and HUD cursor-hiding paths, and stopping passive touch pointer sync from snapping back into the browser-only bounds while keeping controller-driven movement clamped inside the content area.
- Files: `common.py`, `gamepad_cursor.py`, `hud_overlay.py`, `kiosk-wrapper.html`, `start_kiosk_components.sh`, `.xinitrc`, `files/xinitrc`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/common.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/hud_overlay.py`, ran `bash -n /home/pi/gamehub-console/start_kiosk_components.sh /home/pi/gamehub-console/launch_chromium.sh /home/pi/gamehub-console/restart_kiosk.sh /home/pi/.xinitrc /home/pi/gamehub-console/files/xinitrc`, restarted `knf-kiosk.service`, force-killed the stale pre-restart `startx` session so systemd could complete the restart, confirmed the service returned `active (running)` at `17:29:33 +08`, confirmed the relaunched session has fresh `openbox`, `hud_overlay.py`, `gamepad_cursor.py`, and Chromium processes with no new `unclutter` process, checked `logs/cursor.log` for the touchscreen-visible cursor path, and verified `DISPLAY=:0 xdotool getmouselocation --shell` succeeds in the relaunched X session.

## 2026-04-01 15:41:37 +08
- Summary: Replaced the old phone-style Onboard keyboard with a new console-style `QWERTY` layout and dark theme, added Kenney-based Xbox prompt assets plus composite prompt glyphs for the special keys, wired the bottom-row `Paste` action through `xdotool`, and updated the live/install-time Onboard defaults to use the new `gamepad_keyboard` and `gamepad_dark` assets.
- Files: `gamepad_keyboard.onboard`, `gamepad_keyboard.svg`, `gamepad_dark.theme`, `gamepad_dark.colors`, `osk_paste.py`, `gamepad_cursor.py`, `install_gamehub_console.sh`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/.config/onboard/onboard.conf`, `assets/input-prompts/xbox-series/hud/`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/osk_paste.py`, ran `bash -n /home/pi/gamehub-console/install_gamehub_console.sh`, parsed `gamepad_dark.theme`, `gamepad_dark.colors`, `gamepad_keyboard.svg`, and `gamepad_keyboard.onboard` with `xml.etree.ElementTree`, checked that every key in `gamepad_keyboard.onboard` has matching SVG geometry and that every absolute image reference exists, confirmed the generated prompt PNG sizes with Pillow, synced the new layout/theme into `/home/pi/.local/share/onboard/{layouts,themes}`, updated `/home/pi/.config/onboard/onboard.conf` to `layout=gamepad_keyboard` and `theme=gamepad_dark`, and launched `onboard` briefly on `DISPLAY=:0` with the new layout/theme to confirm it starts without any layout/theme parse errors beyond the existing `mousetweaks` and `libayatana-appindicator` warnings.

## 2026-04-01 15:12:46 +08
- Summary: Updated `AGENTS.md` so future on-screen keyboard work follows the attached console-style Image #1 reference, clarifying that the current `Onboard` runtime is still in use but the target OSK design should use the image's full-width gamepad-first layout, dark sharp-corner keys, strong focus state, and console utility row instead of the old phone-style assumptions.
- Files: `AGENTS.md`, `timestamp-console.md`.
- Verification: Reviewed the current OSK integration paths in `gamepad_cursor.py`, `install_gamehub_console.sh`, and `GameHubPhone.onboard`, then updated the repo guidance and OSK verification rules in `AGENTS.md` to point future implementation work at Image #1.

## 2026-04-01 14:39:48 +08
- Summary: Replaced the Bluetooth settings row's preview-only behavior with live controller-driven Bluetooth power, nearby device scan, pair/connect and disconnect actions, added connected-device status tracking, and surfaced a transient `{Device Name} - Connected` HUD toast when a device comes online.
- Files: `hud_overlay.py`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`, ran `python3 - <<'PY' ... hud_overlay.build_status_snapshot() ... PY` to confirm the live snapshot now includes Bluetooth connection metadata, ran `python3 - <<'PY' ... hud_overlay.nearby_bluetooth_devices(scan_seconds=0/1) ... PY` to confirm the new Bluetooth discovery parser returns structured paired and scanned devices, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and `launch_chromium.sh` processes; real pair/connect/disconnect flow plus the toast still need on-device interaction with an actual Bluetooth peripheral in the running kiosk UI.

## 2026-04-01 13:03:26 +08
- Summary: Added a minimum `10%` clamp to the live Settings brightness control so the slider can no longer dim the panel all the way to black while still keeping the real backlight path active.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`; the live floor behavior still needs an on-device controller check in the running Settings overlay.

## 2026-04-01 13:01:33 +08
- Summary: Fixed the live Settings `Brightness` row by switching it from the unreliable X11-only path to the real DSI hardware backlight devices under `/sys/class/backlight`, added a narrow sudo-approved `set_backlight.sh` helper for privileged writes, and updated the HUD brightness logic to drive all matching active DSI backlight nodes together.
- Files: `hud_overlay.py`, `set_backlight.sh`, `files/gamehub-console-sudoers`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`, ran `bash -n /home/pi/gamehub-console/set_backlight.sh`, validated `files/gamehub-console-sudoers` with `visudo -c -f`, installed it to `/etc/sudoers.d/gamehub-console`, confirmed live DSI backlight writes and readback through `/sys/class/backlight/10-0045` and `/sys/class/backlight/11-0045`, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes under the reloaded kiosk session.

## 2026-04-01 12:49:42 +08
- Summary: Converted the bottom-dock `Select` and `Navigate` prompt PNGs to the same monochrome white Kenney prompt style already used by the `X` prompt so the left-side HUD hints now render in a consistent black-and-white treatment.
- Files: `assets/input-prompts/xbox-series/hud/a.png`, `assets/input-prompts/xbox-series/hud/dpad.png`, `timestamp-console.md`.
- Verification: Rewrote both PNGs in place, checked their pixel data with Pillow to confirm the visible pixels are now white-only RGBA values matching the existing `x.png` style while preserving the original `18x18` silhouettes, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, `launch_chromium.sh`, and Chromium processes under the relaunched kiosk session.

## 2026-04-01 12:36:00 +08
- Summary: Removed the `Cursor Sensitivity` row from the Settings menu, hid slider endpoint labels in the live dropdown panels, made `Brightness` drive real display brightness through X11 output brightness with optional `console.env` overrides, and moved the bottom-bar `Bookmark` and `Search` hints into the left-side HUD group.
- Files: `hud_overlay.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`; live `DISPLAY=:0` brightness writes and the updated bottom-dock layout still need on-device visual verification.

## 2026-03-31 16:43:26 +08
- Summary: Added a standalone `settings_gui.py` X11/Tkinter preview that renders the settings menu as a static content-area screen based on the supplied reference, without wiring any real functionality into the HUD or controller flow.
- Files: `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py` and `timeout 2s env DISPLAY=:0 python3 /home/pi/gamehub-console/settings_gui.py` to confirm the Tkinter preview launches on X11 without an immediate traceback.

## 2026-03-31 16:36:26 +08
- Summary: Cleaned up `AGENTS.md` to remove conflicting settings guidance, clarify that `settings_layout.png` is future design guidance only, and separate the default `web-shell/` shell prototype rules from explicit settings-mockup exceptions.
- Files: `AGENTS.md`, `timestamp-console.md`.
- Verification: Reviewed the updated repository instructions for consistent ownership, layout-reference, and testing guidance.

## 2026-03-31 15:19:22 +08
- Summary: Removed the live Settings runtime feature from the HUD so no settings menu, controller toggle path, or alternate footer state remains, while keeping the bottom-right `Settings` label visible as a static dock element.
- Files: `hud_overlay.py`, `AGENTS.md`, `README.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`.

## 2026-03-31 14:22:00 +08
- Summary: Updated the bottom HUD dock to match the settings reference screen more closely by swapping the normal `Settings` prompt into a settings-specific footer mode with `A Select`, `Navigate`, and `B Back` while the Settings menu is open.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`.

## 2026-03-31 13:51:35 +08
- Summary: Wired the Settings `Volume` row to the real system mixer, switched it to smaller stepped changes, and queued mapped `amixer` updates behind a smooth HUD slider transition so volume adjustments feel less jumpy.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`.

## 2026-03-31 13:44:11 +08
- Summary: Restyled the live HUD Settings overlay to match the supplied fullscreen settings reference, including the back-button header, large stacked rows, inverted focused card treatment, and removal of the in-menu footer hint bar in favor of transient action toasts.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`.

## 2026-03-31 12:40:27 +08
- Summary: Restored `AGENTS.md` and `timestamp-console.md` after they were accidentally removed during image-size cleanup, and preserved the current HUD font/animation documentation for future kiosk work.
- Files: `AGENTS.md`, `timestamp-console.md`.
- Verification: Recovered both files from local Codex session history and restored them under `/home/pi/gamehub-console/`.

## 2026-03-31 12:32:42 +08
- Summary: Set the HUD text defaults to the bottom-bar `FF DIN` style and aligned the top clock text to the same font tuple so kiosk text styling stays consistent.
- Files: `hud_overlay.py`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, restarted `knf-kiosk.service`, and confirmed the service returned to `active (running)` with fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes.

## 2026-03-31 12:18:43 +08
- Summary: Animated the Settings overlay between a compact centered state and a fullscreen content-area state on open/close, and hid the pointer across the HUD while the menu is open.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`.

## 2026-03-30 10:36:01 +08
- Summary: Switched the kiosk to a `1024x600` logical desktop and Chromium viewport while keeping the physical DSI panel at `800x480` with X11 scaling.
- Files: `console.env`, `common.py`, `launch_chromium.sh`, `display_mode.sh`, `restart_kiosk.sh`, `files/openbox/autostart`, `/home/pi/.config/openbox/autostart`.
- Verification: Checked `xrandr --current`, Chromium window geometry with `xdotool`, and live viewport values through the Chromium DevTools remote debugging endpoint.

## 2026-03-30 10:36:01 +08
- Summary: Added `timestamp-console.md` and documented the requirement in `AGENTS.md` to record future kiosk changes here.
- Files: `timestamp-console.md`, `AGENTS.md`.
- Verification: Manual documentation review.

## 2026-03-30 10:41:39 +08
- Summary: Restored the kiosk runtime to the `800x480` console layout from `AGENTS.md` and fixed Chromium text-input OSK detection so hosted website inputs can open the keyboard on controller click or touchscreen tap.
- Files: `console.env`, `common.py`, `display_mode.sh`, `launch_chromium.sh`, `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `bash -n` on the shell scripts, `python3 -m py_compile` on the Python files, confirmed live `xrandr` back at `800x480`, confirmed the Chromium window at `800x432`, confirmed DevTools page/iframe viewports (`800x432` wrapper and `1024x600` hosted site), and verified `gamepad_cursor.get_input_focus_state()` plus `install_input_blur_hook()` against a temporary focused input injected into the hosted iframe target.

## 2026-03-30 10:45:00 +08
- Summary: Moved both Onboard launch paths up so the OSK no longer overlaps the 24px bottom HUD bar while keeping the browser content area at `800x432`.
- Files: `gamepad_cursor.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Confirmed the live Chromium window remains `800x432` at `y=24` and updated the OSK geometry to end above the bottom bar.

## 2026-03-30 11:10:18 +08
- Summary: Added the floating Quick Menu overlay to `hud_overlay.py`, routed Start-button control to that HUD menu, added direct settings-tab launches, and suppressed Chromium controller input while the Quick Menu or settings overlay is active.
- Files: `common.py`, `hud_overlay.py`, `gamepad_cursor.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile hud_overlay.py gamepad_cursor.py settings_gui.py common.py`, verified the `GAMEHUB_SETTINGS_TAB` hook and shared Quick Menu state helpers, restarted `hud_overlay.py` and `gamepad_cursor.py`, confirmed Chromium stayed at `800x432`, and opened then closed the live Quick Menu through the bottom navigation hint while observing the shared active flag and the extra Tk overlay window in `xwininfo -root -tree`.

## 2026-03-30 11:49:34 +08
- Summary: Moved HUD status polling off the Tk main thread so Start/Menu presses can open the Quick Menu and launch settings without waiting on Wi-Fi, Bluetooth, volume, or battery subprocess calls.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile hud_overlay.py`, measured status command timings locally, and confirmed the Quick Menu now reads cached status/volume data instead of polling synchronously on button press.

## 2026-03-30 12:03:24 +08
- Summary: Restored `Start` to directly toggle the settings overlay, moved the Quick Menu to the controller `Mode`/Guide button, updated the bottom-right HUD hint to `Settings`, and sped up analog cursor movement with a stronger acceleration curve.
- Files: `gamepad_cursor.py`, `hud_overlay.py`, `AGENTS.md`, `README.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile gamepad_cursor.py hud_overlay.py settings_gui.py common.py`, confirmed `settings_gui.py` still opens at `800x432+0+24` under `DISPLAY=:0`, verified the live gamepad exposes `BTN_START` and `BTN_MODE`, and restarted `hud_overlay.py` plus `gamepad_cursor.py`.

## 2026-04-01 16:16:00 +08
- Summary: Fixed the custom Onboard keyboard so Chromium text inputs can bring it back onscreen reliably, replaced the broken image-only Backspace and Enter keys with text labels, converted Caps Lock to a text label that shares a smaller modifier size group with Shift, removed the broken emoji action that was leaving keys visually stuck, and updated kiosk restarts to properly recycle the Python-hosted `Onboard` process.
- Files: `gamepad_cursor.py`, `gamepad_keyboard.onboard`, `start_kiosk_components.sh`, `restart_kiosk.sh`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile gamepad_cursor.py`, ran `bash -n start_kiosk_components.sh restart_kiosk.sh`, parsed the OSK XML assets, launched the live Chromium/Onboard setup, and captured X11 screenshots to verify the OSK appears over Chromium with the updated labels.

## 2026-04-01 16:29:00 +08
- Summary: Restored the controller-driven mouse path in the kiosk helper so analog cursor movement, click, scroll, and the existing controller button mappings work again while keeping the pointer hidden at all times through the existing kiosk cursor-hiding setup.
- Files: `gamepad_cursor.py`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile gamepad_cursor.py`, restarted the live kiosk components, and confirmed the updated `gamepad_cursor.py` process is running again under the kiosk session.

## 2026-03-30 12:24:00 +08
- Summary: Removed the live kiosk settings feature, deleted `settings_gui.py`, left the bottom-right HUD `Settings` prompt visible, and trimmed the Quick Menu down to volume, restart, and exit actions.
- Files: `gamepad_cursor.py`, `hud_overlay.py`, `common.py`, `install_gamehub_console.sh`, `README.md`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile gamepad_cursor.py hud_overlay.py common.py`, restarted `knf-kiosk.service`, confirmed new `startx`, `hud_overlay.py`, and `gamepad_cursor.py` PIDs under the relaunched service, and confirmed no `settings_gui.py` process remained after restart.

## 2026-03-30 12:44:56 +08
- Summary: Rebuilt the HUD Quick Menu as a six-item floating panel with FF DIN styling, pink-purple focus state, a blue bottom-nav Quick Menu trigger, restored settings launches, and re-enabled controller input blocking while settings are open.
- Files: `common.py`, `gamepad_cursor.py`, `hud_overlay.py`, `settings_gui.py`, `install_gamehub_console.sh`, `README.md`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile common.py gamepad_cursor.py hud_overlay.py settings_gui.py`, replaced the live `hud_overlay.py` and `gamepad_cursor.py` daemons and confirmed new PIDs, and started `settings_gui.py` under `timeout 2s` with `GAMEHUB_SETTINGS_TAB=wifi` on `DISPLAY=:0` to confirm the launcher path and tab hook came up without an immediate traceback.

## 2026-03-30 13:00:36 +08
- Summary: Reverted the broken `12:44:56 +08` HUD/settings change set by removing the restored `settings_gui.py` wrapper, trimming the Quick Menu back to `Volume Control`, `Restart Kiosk`, and `Exit`, restoring the bottom-right HUD `Settings` prompt, and limiting controller input blocking to the Quick Menu again.
- Files: `common.py`, `gamepad_cursor.py`, `hud_overlay.py`, `install_gamehub_console.sh`, `README.md`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile common.py gamepad_cursor.py hud_overlay.py`, ran `bash -n install_gamehub_console.sh`, restarted `knf-kiosk.service`, confirmed the service returned to `active (running)` after the stop timeout cleared, verified new `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher PIDs under the relaunched kiosk session, and confirmed no `settings_gui.py` process was running.

## 2026-03-30 13:11:58 +08
- Summary: Reworked the floating kiosk overlay into a design-only `Settings` menu with `Wi-Fi`, `Bluetooth`, `Volume`, `Restart Kiosk`, and `Shutdown Kiosk` rows, added live status text for the network/audio rows, enabled the bottom-nav `Settings` prompt plus controller `Start`/`Mode` toggles, and kept the non-volume actions as preview messaging only.
- Files: `hud_overlay.py`, `README.md`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile common.py gamepad_cursor.py hud_overlay.py`, restarted `knf-kiosk.service`, confirmed the service returned to `active (running)` after the stop timeout cleared, and verified new `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher PIDs under the relaunched kiosk session.

## 2026-03-30 15:36:02 +08
- Summary: Replaced the HUD and floating Settings menu icon rendering with PNG-backed assets from `icons/`, including clock, Wi-Fi, Bluetooth, volume, battery, restart, shutdown, and the bottom-right `Settings` hint.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`.

## 2026-03-30 15:54:40 +08
- Summary: Stopped downscaling the `icons/` PNGs in `hud_overlay.py` so the HUD and Settings menu use the native `24x24` icon art, and swapped the bottom-right HUD `Settings` prompt icon to the Xbox Start PNG.
- Files: `hud_overlay.py`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, restarted `hud_overlay.py`, and captured a live `scrot` screenshot on `DISPLAY=:0` to confirm the top HUD icons render at native size and the bottom-right `Settings` label shows the Start prompt.

## 2026-03-30 16:32:29 +08
- Summary: Removed the kiosk wrapper letterbox scaling so the hosted website fills the full Chromium viewport instead of being constrained to a centered `1024x600` iframe with left/right black bars.
- Files: `kiosk-wrapper.html`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/common.py`, reloaded Chromium with `bash /home/pi/gamehub-console/restart_kiosk.sh`, confirmed via the DevTools endpoint that both the wrapper page and hosted iframe now report `800x360`, confirmed the wrapper iframe bounds are `x=0`, `y=0`, `width=800`, `height=360`, and confirmed the hosted page root also spans `800x360` with no narrower content box.

## 2026-03-30 16:34:58 +08
- Summary: Restored the HUD top bar to `24px`, rescaled the top-bar status PNGs from `assets/icons/` down to a HUD-sized render target, and aligned the Chromium viewport geometry back to the 24px top dock.
- Files: `common.py`, `console.env`, `launch_chromium.sh`, `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/common.py /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py`, ran `bash -n /home/pi/gamehub-console/launch_chromium.sh`, loaded the top-bar `assets/icons` paths through Tk on `DISPLAY=:0` to confirm they now resolve at `16x16`, restarted `knf-kiosk.service`, waited through the service stop timeout, confirmed the kiosk returned to `active (running)` with a new `MainPID`, and confirmed via the DevTools endpoint that both the wrapper page and hosted iframe now report `800x432`.

## 2026-03-30 16:42:25 +08
- Summary: Replaced the HUD top-bar icon downscale path with smooth `GdkPixbuf` resampling and alpha-preserving tinting so the `16px` status icons fit the `24px` dock without the pixelated nearest-neighbor look.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, loaded the HUD icon paths through Tk on `DISPLAY=:0` to confirm they still resolve at `16x16`, restarted `hud_overlay.py`, and captured `/tmp/hud-top.png` from `DISPLAY=:0` to confirm the live top-bar icons render smoothly.

## 2026-03-30 16:49:18 +08
- Summary: Added a persistent kiosk-side DevTools viewport-fit override in `gamepad_cursor.py` so fixed-size hosted `.gbl-viewport` layouts stretch to the live Chromium content area and no longer leave top/bottom or left/right bars inside the browser region.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, inspected the live hosted DOM over the Chromium DevTools endpoint, confirmed the original `.gbl-viewport` measured `800x384` at `y=24` with `transform: matrix(0.8, 0, 0, 0.8, 0, 0)`, tested the injected override live, confirmed `.gbl-viewport` then measured `800x432` at `y=0` with `transform: matrix(0.8, 0, 0, 0.9, 0, 0)`, restarted `gamepad_cursor.py`, reloaded Chromium with `bash /home/pi/gamehub-console/restart_kiosk.sh`, confirmed after reload that the hosted `.gbl-viewport` still measures `800x432` at `y=0`, and captured `/tmp/browser-area.png`, `/tmp/browser-area-fixed.png`, and `/tmp/browser-area-postfix.png` from `DISPLAY=:0` to confirm the browser area fills without the prior top/bottom bars.

## 2026-03-30 16:53:45 +08
- Summary: Resized the Settings menu row icons to a compact menu-specific target and tightened the row/slider spacing so the overlay fits more cleanly without oversized icon art dominating the panel.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, loaded the Settings menu icon paths through Tk on `DISPLAY=:0` to confirm they now resolve at `36x36`, restarted `hud_overlay.py`, opened the live Settings overlay from the bottom-right prompt, and compared `/tmp/settings-menu-before.png` against `/tmp/settings-menu-after.png` to confirm the rows now use compact icon sizing with cleaner spacing.

## 2026-03-30 17:06:06 +08
- Summary: Constrained controller-driven mouse cursor movement in `gamepad_cursor.py` so the stick-controlled pointer stays inside the main content area and cannot enter the `24px` top HUD or `24px` bottom navigation bar.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, restarted `gamepad_cursor.py`, forced the pointer to `Y=0` and `Y=479` on `DISPLAY=:0`, invoked the live movement clamp path, and confirmed it snaps back to `Y=24` at the top bound and `Y=455` at the bottom bound.

## 2026-03-30 17:33:44 +08
- Summary: Built a `GameHubCursor` Xcursor theme from the provided cursor PNG, installed it into `~/.icons`, and updated the X11 startup plus installer paths so the kiosk session now boots with the resized custom pointer at `32px`.
- Files: `.xinitrc`, `files/xinitrc`, `install_gamehub_console.sh`, `assets/cursor-theme/GameHubCursor/`, `timestamp-console.md`.
- Verification: Installed `x11-apps` and `python3-pil`, generated `24px`, `32px`, and `48px` cursor assets plus a compiled `default` Xcursor file, installed the live theme under `~/.icons/GameHubCursor`, restarted `knf-kiosk.service`, confirmed the new kiosk session came back active at `17:36:35 +08`, verified the relaunched HUD, controller, and Chromium launcher processes now inherit `XCURSOR_THEME=GameHubCursor` with `XCURSOR_SIZE=32`, and removed the one stale detached pre-restart `gamepad_cursor.py` process.

## 2026-03-30 17:41:28 +08
- Summary: Disabled browser zoom in kiosk mode by adding Chromium's pinch-disable flag, locking the wrapper viewport to scale `1`, and extending the DevTools-injected browser fixes so hosted pages reject `Ctrl` plus mouse-wheel zoom, keyboard zoom shortcuts, and multitouch pinch gestures.
- Files: `launch_chromium.sh`, `kiosk-wrapper.html`, `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `bash -n /home/pi/gamehub-console/launch_chromium.sh`, ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, restarted `knf-kiosk.service`, confirmed the new kiosk session came back active at `17:44:12 +08`, verified the relaunched Chromium command line now includes `--disable-pinch`, confirmed the wrapper plus hosted page targets report the zoom-lock injection as installed with a `maximum-scale=1` / `user-scalable=no` viewport, and checked that a simulated `Ctrl` plus mouse-wheel input no longer changes the hosted page `devicePixelRatio` (`1` before and after).

## 2026-03-30 18:07:34 +08
- Summary: Rebuilt the `GameHubCursor` Xcursor theme from `assets/icons/hud/cursor.png`, keeping the existing kiosk cursor footprint and hotspot sizing so the provided pink/orange cursor art replaces the old outline pointer without changing the `32px` on-screen fit.
- Files: `assets/cursor-theme/build/default-24.png`, `assets/cursor-theme/build/default-32.png`, `assets/cursor-theme/build/default-48.png`, `assets/cursor-theme/GameHubCursor/cursors/default`, `timestamp-console.md`.
- Verification: Regenerated the `24px`, `32px`, and `48px` cursor PNGs from `/home/pi/gamehub-console/assets/icons/hud/cursor.png` while preserving the prior bounding boxes `24:(1,1,17,23)`, `32:(1,1,23,31)`, and `48:(2,2,35,46)`, rebuilt the compiled cursor with `xcursorgen`, installed it into `/home/pi/.icons/GameHubCursor/cursors/default`, restarted `knf-kiosk.service`, and confirmed the kiosk session returned `active (running)` at `18:06:57 +08` with fresh `startx`, `openbox`, `hud_overlay.py`, `gamepad_cursor.py`, and Chromium processes.

## 2026-03-31 15:41:24 +08
- Summary: Reworked the analog cursor motion path in `gamepad_cursor.py` to calibrate stick range per controller, apply radial deadzone handling with time-based smoothing, and accumulate fractional pixels so pointer movement is more accurate at low stick deflection while staying smooth at higher speed.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py /home/pi/gamehub-console/hud_overlay.py`.

## 2026-03-31 17:01:35 +08
- Summary: Re-enabled the runtime Settings overlay in `hud_overlay.py`, wired it to `Start` and `B`, matched the five-row design to `settings_layout.png`, and kept every row layout-only so the menu opens, highlights, and closes without triggering real system actions.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py /home/pi/gamehub-console/settings_gui.py`.

## 2026-03-31 17:17:44 +08
- Summary: Expanded the layout-only Settings menu to seven items in the requested order by adding `Cursor Sensitivity` and `Brightness`, reordering the existing rows, and updating the standalone preview to match the new list.
- Files: `hud_overlay.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py`, restarted `knf-kiosk.service`, confirmed the relaunched kiosk session returned `active (running)` at `17:20:58 +08`, and verified fresh `startx`, `openbox`, `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes under the new `17:21` session.

## 2026-03-31 17:29:05 +08
- Summary: Removed the header back arrow from the Settings screen and changed the active bottom-right prompt so it keeps the `Start` icon while relabeling it to `Back`.
- Files: `hud_overlay.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py`, restarted `knf-kiosk.service`, confirmed the relaunched kiosk session returned `active (running)` at `17:31:48 +08`, and verified fresh `startx`, `openbox`, `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes under the new `17:31` session.

## 2026-03-31 17:34:45 +08
- Summary: Made the `Volume` row in the Settings overlay functional by restoring in-menu adjust mode, live system volume writes, and the inline volume slider while leaving the other settings rows layout-only.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py /home/pi/gamehub-console/settings_gui.py`, confirmed `amixer get Master` exposes a writable `Master` mixer, restarted `knf-kiosk.service`, confirmed the relaunched kiosk session returned `active (running)` at `17:37:25 +08`, and verified fresh `startx`, `openbox`, `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes under the new `17:37` session.

## 2026-03-31 17:47:51 +08
- Summary: Restyled the Settings screen to the new brand palette by switching to the deep `#130b0f` page background, `#1e1219` sub-panel, bordered `#2a2435` cards, muted unfocused icons/values, orange destructive labels, pink Back-state accenting, and the `#f0184e` to `#f5793a` gradient for the focused row.
- Files: `hud_overlay.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py`, restarted `knf-kiosk.service`, confirmed the relaunched kiosk session returned `active (running)` at `17:47:42 +08`, and verified fresh `startx`, `openbox`, `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes under the new `17:47` session.

## 2026-03-31 17:53:09 +08
- Summary: Reduced the Settings overlay open-time lag by replacing the per-pixel focus gradient draw with a cheaper banded gradient and by stopping row rerenders during the open/close animation until the final frame.
- Files: `hud_overlay.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py`, restarted `knf-kiosk.service`, confirmed the relaunched kiosk session returned `active (running)` at `17:55:45 +08`, and verified fresh `startx`, `openbox`, `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes under the new `17:55` session.

## 2026-03-31 18:03:55 +08
- Summary: Added a daily rollback-backup job by creating `backup_rollback_zip.sh`, wiring it into `install_gamehub_console.sh`, and installing a managed cron schedule that rebuilds `/home/pi/kiosk-backup-latest.zip` every day at `17:00` in `Asia/Kuala_Lumpur` from the stable kiosk paths while excluding `.codex`, prior backup zips, live logs, and `__pycache__`.
- Files: `backup_rollback_zip.sh`, `files/gamehub-console-backup.cron`, `install_gamehub_console.sh`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Confirmed the system timezone is `Asia/Kuala_Lumpur (+08)`, installed `/etc/cron.d/gamehub-console-backup`, restarted `cron`, ran `bash /home/pi/gamehub-console/backup_rollback_zip.sh`, verified `/home/pi/kiosk-backup-latest.zip` was rebuilt successfully at `18:09 +08`, and verified with Python `zipfile` that the archive contains the kiosk paths only, with no `.codex` entries and no live `gamehub-console/logs/*` files.

## 2026-04-01 10:01:45 +08
- Summary: Reworked the live Settings overlay in `hud_overlay.py` so pressing `A` on the highlighted row opens a dropdown panel under that row, added a real volume slider, preview-only WiFi and Bluetooth nearby lists, preview-only cursor sensitivity and brightness sliders, brightness icon tinting from dark to light, and two-step `Confirm?` panels for restart and shutdown with live reboot/poweroff actions on confirmation.
- Files: `hud_overlay.py`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`, restarted `knf-kiosk.service`, confirmed it returned `active (running)` at `10:01:36 +08`, and verified fresh `startx`, `hud_overlay.py`, `gamepad_cursor.py`, and Chromium processes under the new session.

## 2026-04-01 10:11:45 +08
- Summary: Centered the active Settings row in the live overlay scroll viewport, renamed the destructive restart row to `Restart Kiosk`, and changed its action to restart `knf-kiosk.service` so the kiosk session, browser, HUD, and controller daemons relaunch without rebooting the Pi.
- Files: `hud_overlay.py`, `restart_kiosk.sh`, `settings_gui.py`, `files/gamehub-console-sudoers`, `README.md`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`, ran `bash -n /home/pi/gamehub-console/restart_kiosk.sh`, validated `files/gamehub-console-sudoers` with `visudo -c -f`, installed it to `/etc/sudoers.d/gamehub-console`, restarted `knf-kiosk.service`, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` to verify the menu’s kiosk-only restart path; after the final restart, confirmed fresh `startx`, `hud_overlay.py`, `gamepad_cursor.py`, and Chromium processes under the new `10:21 +08` session.

## 2026-04-01 10:39:28 +08
- Summary: Reworked `Restart Kiosk` into a fast in-session recycle that kills and relaunches the HUD, controller daemon, and Chromium under the existing Openbox session, added a shared `start_kiosk_components.sh` launcher for both Openbox autostart and manual restarts, and changed the Settings overlay scrolling so the list stays pinned near the top until the highlighted row crosses the viewport midpoint and only then scrolls downward.
- Files: `start_kiosk_components.sh`, `restart_kiosk.sh`, `hud_overlay.py`, `install_gamehub_console.sh`, `files/openbox/autostart`, `/home/pi/.config/openbox/autostart`, `files/gamehub-console-sudoers`, `README.md`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`, ran `bash -n /home/pi/gamehub-console/start_kiosk_components.sh /home/pi/gamehub-console/restart_kiosk.sh`, validated `files/gamehub-console-sudoers` with `visudo -c -f`, installed it to `/etc/sudoers.d/gamehub-console`, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` outside the sandbox to verify the live fast-restart path; confirmed the original `10:24` HUD/controller/browser launcher PIDs were replaced by fresh `10:38` PIDs while the existing Openbox PID `25945` stayed alive, and confirmed Chromium relaunched again with a new `--app=file:///home/pi/gamehub-console/kiosk-wrapper.html#...` process.

## 2026-04-01 10:52:25 +08
- Summary: Adjusted the live Settings overlay input handling so pressing the highlighted row no longer auto-snaps the list to center, added touch drag scrolling on the settings list with tap-versus-scroll separation so vertical touch scrolls do not trigger the row action, and fixed a `restart_kiosk.sh` lock-file-descriptor leak that was preventing repeated fast kiosk restarts from recycling the live HUD/controller/browser stack.
- Files: `hud_overlay.py`, `restart_kiosk.sh`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`, ran `bash -n /home/pi/gamehub-console/restart_kiosk.sh /home/pi/gamehub-console/start_kiosk_components.sh`, force-cleared the stale pre-fix lock holder by terminating the remaining `10:38` kiosk PIDs, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` outside the sandbox and confirmed fresh `10:55 +08` `hud_overlay.py`, `gamepad_cursor.py`, `launch_chromium.sh`, and Chromium PIDs under the existing Openbox session.

## 2026-04-01 10:56:37 +08
- Summary: Updated the kiosk target URL to `https://limegreen-partridge-237325.hostingersite.com/?mode=handheld` in the live config and all local fallback launch paths so Chromium and the wrapper both default to the handheld site mode.
- Files: `console.env`, `common.py`, `launch_chromium.sh`, `kiosk-wrapper.html`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/common.py`, ran `bash -n /home/pi/gamehub-console/launch_chromium.sh`, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` to reload the live kiosk with the new URL.

## 2026-04-01 11:04:25 +08
- Summary: Restored instant recentering when pressing `A` on the highlighted Settings row, replaced the jagged spline-based rounded outlines with arc-and-line rounded borders in both the live overlay and the standalone preview, and updated the local kiosk guidance to match the new input behavior.
- Files: `hud_overlay.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`, ran `timeout 3s env DISPLAY=:0 python3 /home/pi/gamehub-console/settings_gui.py` to confirm the preview still opens on X11 without an immediate traceback, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed fresh live `hud_overlay.py`, `gamepad_cursor.py`, `launch_chromium.sh`, and Chromium processes under the relaunched kiosk session.

## 2026-04-01 11:32:09 +08
- Summary: Tightened the Settings card rendering so the border is drawn as the outer rounded shell and the fill is inset inside it, preventing the focused gradient and other card fills from bleeding outside their rounded borders in both the live overlay and the standalone preview.
- Files: `hud_overlay.py`, `settings_gui.py`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`, then ran `timeout 3s env DISPLAY=:0 python3 /home/pi/gamehub-console/settings_gui.py` to confirm the preview still opens on X11 without an immediate traceback.

## 2026-04-01 11:46:27 +08
- Summary: Switched the Settings option cards to sharp corners in both the live overlay and the standalone preview, reduced the volume and brightness slider step sizes for smoother motion, and added held D-pad repeat so those sliders continue changing while the direction is held.
- Files: `hud_overlay.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py /home/pi/gamehub-console/common.py`, ran `timeout 3s env DISPLAY=:0 python3 /home/pi/gamehub-console/settings_gui.py` to confirm the preview still opens on X11 without an immediate traceback, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed fresh live `hud_overlay.py`, `gamepad_cursor.py`, `launch_chromium.sh`, and Chromium processes under the relaunched kiosk session.

## 2026-04-01 11:54:39 +08
- Summary: Added Kenney Xbox Series `X` and `Y` prompt PNGs to the HUD prompt asset folder and extended the bottom navigation dock to show `X Bookmark` and `Y Search` hints alongside the existing `Settings` prompt.
- Files: `assets/input-prompts/xbox-series/hud/x.png`, `assets/input-prompts/xbox-series/hud/y.png`, `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/common.py`, then ran a short `DISPLAY=:0` Tk load check to confirm both new prompt PNGs open at `18x18` without error.

## 2026-04-01 16:29:21 +08
- Summary: Fixed the restored controller-mouse helper startup by switching the stale `KioskInputHelper` entry point to the current `Controller` class so the analog mouse, click, and scroll path now launches again while the kiosk keeps the cursor hidden through `unclutter` and the existing UI-level cursor suppression.
- Files: `gamepad_cursor.py`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, ran `bash -n /home/pi/gamehub-console/start_kiosk_components.sh /home/pi/gamehub-console/restart_kiosk.sh`, ran `/home/pi/gamehub-console/restart_kiosk.sh`, and confirmed fresh `16:28:32 +08` `unclutter`, `gamepad_cursor.py`, `launch_chromium.sh`, and `/usr/bin/onboard` processes under the relaunched kiosk session.

## 2026-04-02 14:44:00 +08
- Summary: Restored visible alphanumeric labels on the custom Onboard OSK by reducing the letter/number key `label_margin` values from an over-constrained setting that collapsed the available label box and caused the text to disappear.
- Files: `gamepad_keyboard.onboard`, `timestamp-console.md`.
- Verification: Ran an XML parse check for `/home/pi/gamehub-console/gamepad_keyboard.onboard`, confirmed the updated `label_margin="2,5"` values on the alphanumeric keys, then reloaded the kiosk session with `/home/pi/gamehub-console/restart_kiosk.sh`.

## 2026-04-02 15:00:39 +08
- Summary: Removed the `A to finish` wording from the live Settings slider detail panel and from the matching volume and brightness adjust-mode toast messages so the overlay now shows only the D-pad adjustment hint.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/common.py`, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed fresh live `hud_overlay.py`, `gamepad_cursor.py`, and `launch_chromium.sh` processes under the relaunched kiosk session.

## 2026-04-02 15:14:16 +08
- Summary: Reworked the Settings Bluetooth dropdown spacing so the device-list background has wider side padding, taller rows, and a real bottom margin, which prevents the list entries from crowding the panel border and makes the dropdown fit cleanly.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-151101.md`.
- Verification: Checked the updated list-panel geometry math to confirm a consistent 10px bottom margin remains below the last Bluetooth row, then ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/common.py`, ran `bash /home/pi/gamehub-console/restart_kiosk.sh`, and confirmed fresh live `hud_overlay.py`, `gamepad_cursor.py`, and `launch_chromium.sh` processes under the relaunched kiosk session.

## 2026-04-02 15:18:28 +08
- Summary: Reworked the Restart and Shutdown confirm panels to use the same cleaner outer spacing as the Bluetooth dropdown and increased the confirm-panel height so the `Confirm?` button stays fully inside the panel with a real bottom margin.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-151753.md`.
- Verification: Checked the confirm-panel geometry math to confirm the button now ends 10px above the panel bottom, then ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/common.py`, ran `bash /home/pi/gamehub-console/restart_kiosk.sh`, and confirmed fresh live `hud_overlay.py`, `gamepad_cursor.py`, and `launch_chromium.sh` processes under the relaunched kiosk session.

## 2026-04-02 15:24:07 +08
- Summary: Removed the extra toast popup shown when entering the Volume or Brightness adjust panels so selecting those settings no longer shows the `Volume: D-pad or left/right to adjust` or matching brightness label above the menu.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-152252.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/common.py`, confirmed `open_adjustable()` now clears any previous message instead of setting the adjust-mode toast, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed fresh live `hud_overlay.py`, `gamepad_cursor.py`, and `launch_chromium.sh` processes under the relaunched kiosk session.

## 2026-04-02 15:34:20 +08
- Summary: Fixed Bluetooth placeholder naming so MAC-like labels such as `50-D4-F0-23-87-91` are treated as anonymous devices and rendered as `Unknown [Type]` instead of being shown as raw addresses in the Settings Bluetooth list.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-153301.md`.
- Verification: Ran a Python check with `PYTHONPATH=/home/pi/gamehub-console` to confirm `bluetooth_name_is_placeholder('50-D4-F0-23-87-91', '50:D4:F0:23:87:91')` returns `True` and that the fallback display names resolve to `Unknown [Controller]`, `Unknown [Headphones]`, and `Unknown [Device]`, then ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/common.py`, ran `bash /home/pi/gamehub-console/restart_kiosk.sh`, and confirmed fresh live `hud_overlay.py`, `gamepad_cursor.py`, and `launch_chromium.sh` processes under the relaunched kiosk session.

## 2026-04-02 15:44:31 +08
- Summary: Fixed Bluetooth refresh sorting so placeholder entries like `Unknown [Device]` stay below devices with real names after the final list normalization pass.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-154248.md`.
- Verification: Ran a Python sort check with `PYTHONPATH=/home/pi/gamehub-console` confirming `EMBERTON` sorts above `Unknown [Device]`, then ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/common.py`, ran `bash /home/pi/gamehub-console/restart_kiosk.sh`, and confirmed fresh live `hud_overlay.py`, `gamepad_cursor.py`, and `launch_chromium.sh` processes under the relaunched kiosk session.

## 2026-04-02 16:07:55 +08
- Summary: Canceled the unfinished Bluetooth display-name cleanup that would have stripped a trailing ` [LE]` suffix from device names, restoring the original on-disk `hud_overlay.py` logic before that change was compiled or reloaded into the live kiosk session.
- Files: `hud_overlay.py`, `timestamp-console.md`.
- Verification: Removed the temporary `sanitize_bluetooth_display_name()` helper and restored the original `bluetooth_display_name()` path, then ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/common.py`. No kiosk restart was needed because the running overlay predates the aborted on-disk edit.

## 2026-04-02 16:35:23 +08
- Summary: Turned the Settings Wi-Fi row into a live control flow with radio on/off, nearby network refresh, open-network connect, password-protected connect through a small Onboard-backed popup, and a 1-second `<SSID> - Connected` toast; also split HUD text-entry state from quick-menu blocking so the Wi-Fi password popup can use the current OSK without re-enabling browser-side controller input.
- Files: `common.py`, `gamepad_cursor.py`, `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-163317.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py`, then ran Python import checks with `PYTHONPATH=/home/pi/gamehub-console` confirming `wifi_status()` returned the live SSID tuple, `current_wifi_device()` resolved `wlan0`, `nearby_wifi_networks(rescan=False)` returned the deduped nearby Wi-Fi list, and `wifi_security_requires_password()` distinguished open vs protected sample networks. No kiosk restart was run in this edit turn.

## 2026-04-02 16:50:15 +08
- Summary: Fixed the kiosk-side Wi-Fi authorization failure by routing mutating Wi-Fi `nmcli` actions through the existing passwordless sudoers allowance for `/usr/bin/nmcli`, so the Settings Wi-Fi toggle and connect flow no longer depends on a desktop polkit prompt.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-165015.md`.
- Verification: Confirmed `sudo -n /usr/bin/nmcli -v` succeeds on the live machine, confirmed `/etc/sudoers.d/gamehub-console` includes `/usr/bin/nmcli`, ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py`, and ran a Python import check verifying `nmcli_text(['-t','-f','WIFI','g'])` returns `enabled` while `run_nmcli_output(['-v'], privileged=True)` returns success.

## 2026-04-02 17:13:19 +08
- Summary: Removed the kiosk-owned Bluetooth connected toast window so successful Bluetooth connects no longer raise an extra popup over the kiosk UI.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-171319.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py`, then confirmed no active `bluetooth_toast` or `show_bluetooth_connected_toast` references remain in `hud_overlay.py` and that the remaining Bluetooth connect path only updates menu state.

## 2026-04-02 17:21:51 +08
- Summary: Disabled the OS-level Blueman applet in kiosk sessions and kill it during kiosk launch/restart so Blueman's desktop Bluetooth popup windows no longer appear over the kiosk while using the custom Bluetooth flow.
- Files: `install_gamehub_console.sh`, `start_kiosk_components.sh`, `restart_kiosk.sh`, `/home/pi/.config/autostart/blueman.desktop`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-172151.md`.
- Verification: Ran `bash -n /home/pi/gamehub-console/install_gamehub_console.sh /home/pi/gamehub-console/start_kiosk_components.sh /home/pi/gamehub-console/restart_kiosk.sh`, confirmed `/home/pi/.config/autostart/blueman.desktop` now contains a hidden autostart override, and confirmed `/etc/xdg/autostart/blueman.desktop` was the source of the live `blueman-applet` startup before this change.

## 2026-04-02 17:32:19 +08
- Summary: Fixed Wi-Fi password entry with the current Onboard OSK by preventing the OSK restore path from re-activating Chromium while HUD text entry is active, and by reasserting focus on the Tk password entry after the popup opens.
- Files: `gamepad_cursor.py`, `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-173219.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py`, then confirmed the new `browser_focus_allowed()` gate now blocks `restore_browser_window()` during HUD text entry and that the Wi-Fi password dialog schedules repeated `focus_entry()` calls using `focus_force()` after it is shown.

## 2026-04-02 17:41:21 +08
- Summary: Fixed the remaining Wi-Fi password-entry failure by converting the popup to a managed Tk dialog, parenting it to the Settings overlay window, and explicitly activating the dialog's X window id with `xdotool` so XTest-based Onboard input lands in the password field instead of Chromium.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-174121.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py`, then ran an X11 Tk test using the same `windowmap` / `windowraise` / `windowactivate --sync` pattern and confirmed the focused window changed to `WiFi Password Test` and the injected text `dialogworks` was written into the Tk entry output file.

## 2026-04-02 18:04:13 +08
- Summary: Tightened the Wi-Fi refresh flow so the Settings menu reacts immediately when refresh is pressed: it keeps the current network list visible during the scan, flips the refresh row into its active scanning state right away, and uses a short retry window instead of waiting multiple seconds when the list does not visibly change.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-180413.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py`, then ran a live helper check with `PYTHONPATH=/home/pi/gamehub-console` confirming `refresh_wifi_networks(previous_networks=baseline)` completed in about `0.829s` on the current device instead of stalling for the earlier multi-second timeout path.

## 2026-04-02 18:10:52 +08
- Summary: Fixed the Wi-Fi password popup mapping failure by owning the dialog from the hidden root Tk window instead of the override-redirect Settings overlay, only enabling HUD text-input state after the dialog opens successfully, and surfacing a kiosk error toast if the dialog cannot map.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-181017.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py /home/pi/gamehub-console/settings_gui.py`, ran `bash /home/pi/gamehub-console/restart_kiosk.sh`, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, `launch_chromium.sh`, and Chromium processes with `pgrep -af`. Full on-device protected-WiFi entry should still be checked once from the live Settings menu.

## 2026-04-02 18:21:05 +08
- Summary: Fixed the remaining Wi-Fi password-popup flash by asserting HUD text-input mode before mapping the popup, closing the race where the browser-focus restore loop could immediately reactivate Chromium during the dialog's first frame and hide it behind the kiosk page.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-182058.md`.
- Verification: Confirmed the live X11 tree still exposes the mapped `WiFi Password` window while the browser had focus, patched the state ordering in `open_wifi_password_dialog()`, and will reload the kiosk after `python3 -m py_compile` so the running HUD picks up the timing fix.

## 2026-04-02 18:46:42 +08
- Summary: Replaced the separate Wi-Fi password X11 dialog with an in-overlay modal panel rendered inside the existing Settings window, so the password field can no longer stack underneath Chromium or the Settings overlay while still focusing the Tk entry for Onboard input.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-184646.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py /home/pi/gamehub-console/settings_gui.py`, confirmed the refactored `WifiPasswordDialog` now uses a placed `tk.Frame` modal instead of `tk.Toplevel`, and will reload the kiosk so the live HUD picks up the in-overlay password field.

## 2026-04-02 18:52:22 +08
- Summary: Moved the in-overlay Wi-Fi password modal up to the upper safe area of the Settings overlay so the full panel stays visible above the `180px` Onboard keyboard instead of slightly overlapping it.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260402-185122.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py /home/pi/gamehub-console/common.py /home/pi/gamehub-console/settings_gui.py`, confirmed the modal placement now uses a top-centered `place(..., anchor='n')` path instead of vertical centering, and will reload the kiosk so the live overlay picks up the new placement.

## 2026-04-03 09:40:05 +08
- Summary: Added a show/hide control to the Settings Wi-Fi password popup so users can reveal or re-mask the entered password from the field using the existing Wi-Fi visibility icons.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-094005.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, confirmed the Wi-Fi password dialog now resets to masked mode on open and close, keeps entry focus after toggling visibility, and registers the new toggle button with the overlay cursor widgets, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, `launch_chromium.sh`, and Chromium kiosk processes with `pgrep -af`. Live popup interaction should still be checked from `Settings > WiFi > protected network`.

## 2026-04-03 09:47:24 +08
- Summary: Changed the kiosk website target to `https://handheld.knfstudios.com/?mode=handheld` in the live config and all local fallback launch paths so Chromium and the wrapper default to the new handheld site.
- Files: `console.env`, `common.py`, `launch_chromium.sh`, `kiosk-wrapper.html`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-094724.md`.
- Verification: Updated the configured and fallback URL values together, then reloaded the kiosk so Chromium would relaunch against the new target and verified the live Chromium command line reflects the updated `kiosk-wrapper.html#https://handheld.knfstudios.com/?mode=handheld` URL.

## 2026-04-03 09:52:05 +08
- Summary: Changed the Wi-Fi connect flow to update and reactivate the saved NetworkManager profile for the target SSID before falling back to `device wifi connect`, so switching back to a previously saved secured network does not fail on a stale autogenerated profile with missing `802-11-wireless-security.key-mgmt`.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-095205.md`.
- Verification: Inspected the live `nmcli` profiles and confirmed the kiosk currently has saved secured profiles for both `netplan-wlan0-Todak Guest` and `Mad Fong`, ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, and confirmed the new connect path now selects the saved profile by SSID, refreshes its PSK when a password is provided, and only falls back to direct SSID connect if saved-profile activation fails. I did not run a live network-switch mutation during verification to avoid disrupting the current kiosk connection.

## 2026-04-03 09:58:55 +08
- Summary: Fixed nearby Wi-Fi discovery so the Settings Wi-Fi list and refresh flow use the sudo-approved `nmcli` scan path; this prevents the kiosk session from getting stuck on a stale one-SSID view that only updated after toggling Wi-Fi off and on.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-095855.md`.
- Verification: Compared live scan output on the current device and confirmed raw `nmcli ... dev wifi list --rescan yes` only returned the connected `Todak Guest` SSID, while `sudo -n /usr/bin/nmcli ... --rescan yes` returned the full nearby list including `DT-GBL-01`, `Todak`, `Neo Todak`, `beatdown`, and `Neo 2.4`; then ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py` and confirmed the nearby-network helpers now use the privileged scan and rescan paths.

## 2026-04-03 10:09:01 +08
- Summary: Added touch hit-testing for expanded Wi-Fi and Bluetooth dropdown panels so taps activate the specific touched option instead of falling back to the parent row behavior.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-100901.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, confirmed the touch-release path now resolves row-canvas taps against the expanded dropdown entry rectangles before calling the existing Wi-Fi or Bluetooth activation handlers, and reloaded the kiosk so the live Settings overlay picks up the change. Full manual touch verification should be checked on-device from `Settings > WiFi` and `Settings > Bluetooth`.

## 2026-04-03 10:18:21 +08
- Summary: Changed kiosk startup to launch `unclutter -idle 0 -root` as part of every kiosk session, replacing the earlier touchscreen-conditional path and the extra `-grab -noevents` flags.
- Files: `start_kiosk_components.sh`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-101821.md`.
- Verification: Ran `bash -n /home/pi/gamehub-console/start_kiosk_components.sh /home/pi/gamehub-console/restart_kiosk.sh`, restarted the kiosk, and confirmed the relaunched session includes the expected `unclutter -idle 0 -root` process.

## 2026-04-03 10:21:30 +08
- Summary: Switched the Settings dropdown slider thumb from the old drawn circle to the existing `assets/icons/hud/slider_dot.png` image asset.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-102130.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, confirmed `draw_slider()` now loads and draws `hud/slider_dot.png` as the thumb image with the old vector circle kept only as a fallback, and reloaded the kiosk so the live dropdown sliders pick up the asset-backed thumb.

## 2026-04-03 10:29:44 +08
- Summary: Updated the dropdown slider thumb to tint `slider_dot.png` solid white so the icon reads as a filled white control and fits the dark settings aesthetic more cleanly.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-102944.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, confirmed `draw_slider()` now loads `hud/slider_dot.png` through `load_status_icon(..., TEXT, ...)` so the slider thumb is rendered white in the live UI, and reloaded the kiosk so the running dropdown sliders pick up the new tint.

## 2026-04-03 10:39:01 +08
- Summary: Added a short slide tween to the live Onboard OSK so it animates up from below the screen when shown and slides back down before closing instead of appearing abruptly.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-103508.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, restarted the kiosk, and confirmed fresh `gamepad_cursor.py`, `hud_overlay.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 10:42:10 +08
- Summary: Added consistent left and right outer margins to the live Settings overlay so the header and main settings panel no longer run edge-to-edge across the screen.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-104038.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, restarted the kiosk, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 10:46:06 +08
- Summary: Rounded the live Settings overlay cards and expanded panels so the menu now uses a softer corner treatment across rows, detail containers, list items, and confirm controls.
- Files: `hud_overlay.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-104344.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py`, restarted the kiosk, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 10:50:58 +08
- Summary: Smoothed the live Onboard tween by switching to a gentler easing curve, reducing per-frame window churn to direct moves only, and deferring the restore loop until after the slide animation completes.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-104843.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, restarted the kiosk, and confirmed fresh `gamepad_cursor.py`, `hud_overlay.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 11:02:15 +08
- Summary: Removed the OSK open delay by keeping Onboard prewarmed in the background, reusing the hidden keyboard window instead of killing the process on every hide, and preserving the slide tween on the reused window.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-104843.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, restarted the kiosk, and confirmed fresh `gamepad_cursor.py`, `hud_overlay.py`, Chromium launcher, and `onboard` processes are running in the relaunched session.

## 2026-04-03 11:09:35 +08
- Summary: Replaced the settings-menu rounded card renderer with an antialiased image-backed path so the rounded borders render smoothly and the inner fill follows the same rounded corners instead of showing jagged or square-looking edges.
- Files: `hud_overlay.py`, `settings_gui.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-110728.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/settings_gui.py`, restarted the kiosk, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, Chromium launcher, and `onboard` processes are running in the relaunched session.

## 2026-04-03 11:50:16 +08
- Summary: Removed the boxed prompt border from the bottom-right Settings hint by switching that dock control from the outlined `start.png` asset to the existing borderless drawn menu glyph.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-115016.md`.
- Verification: Confirmed `assets/input-prompts/xbox-series/hud/start.png` contains the visible outline, ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, restarted the kiosk with `./restart_kiosk.sh`, and verified fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 11:56:56 +08
- Summary: Restored the bottom-right Settings hint to the original `start.png` asset so the HUD matches the Image #1 prompt style again.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-115656.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, restarted the kiosk with `./restart_kiosk.sh`, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 11:59:50 +08
- Summary: Hid the grey backing slab behind the Settings utility rows by making the list canvas, list frame, and row canvas surfaces blend into the main menu background instead of `MENU_PANEL_BG`.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-115950.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, restarted the kiosk with `./restart_kiosk.sh`, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 15:10:15 +08
- Summary: Fixed two Settings Bluetooth flow bugs by rendering the scan state immediately when a Bluetooth refresh starts and by running a short nearby rescan after pair/connect attempts so retryable unpaired devices do not disappear from the list right after an action.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-151015.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, ran a Python import check confirming `nearby_bluetooth_devices(scan_seconds=1)` still returns structured live devices on the current Pi, restarted the kiosk with `./restart_kiosk.sh`, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 15:20:31 +08
- Summary: Fixed Bluetooth discovery in the Settings menu by keeping already-known adapter devices in the candidate set instead of dropping them unless they reappeared in the latest short scan, and by labeling remembered-but-not-freshly-scanned entries as `Known`.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-152031.md`.
- Verification: Confirmed the Pi Bluetooth stack is healthy with `systemctl status bluetooth`, `rfkill list bluetooth`, `hciconfig -a`, `lsmod | grep -Ei 'bluetooth|btbcm|hci_uart'`, and `bluetoothctl devices`, ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, ran a `PYTHONPATH=/home/pi/gamehub-console python3` check confirming `nearby_bluetooth_devices(scan_seconds=1)` now returns remembered devices like `MAJOR V [LE]` and `HUAWEI Band 10-1CD` in addition to freshly scanned results, restarted the kiosk with `./restart_kiosk.sh`, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 15:43:54 +08
- Summary: Hardened the Settings Bluetooth flow for common mice, keyboards, controllers, speakers, headsets, headphones, and earbuds by extending the default scan window, raising the visible device budget, priming a short pre-connect scan for LE devices, explicitly using a `KeyboardDisplay` agent with repeated confirmation responses, and lengthening the pair/connect wait windows plus one retry connect pass.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-154354.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, ran `PYTHONPATH=/home/pi/gamehub-console python3` checks confirming the new constants and generated Bluetooth command sequences, confirmed sample names classify as `Keyboard`, `Mouse`, `Controller`, `Headphones`, and `Earbuds`, ran a live `nearby_bluetooth_devices(scan_seconds=1)` probe confirming remembered and freshly scanned devices still populate together under the new flow, then restarted the kiosk with `./restart_kiosk.sh` and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 15:53:45 +08
- Summary: Fixed the Bluetooth pairing `Failed to register agent object` error by removing the duplicate in-script `agent KeyboardDisplay` command and keeping the agent capability registration only on the `bluetoothctl --agent KeyboardDisplay` process startup path.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-155345.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, ran a `PYTHONPATH=/home/pi/gamehub-console python3` check confirming `bluetooth_session_setup_commands()` now returns only `default-agent` and `pairable on`, restarted the kiosk with `./restart_kiosk.sh`, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 15:59:20 +08
- Summary: Updated the top HUD Bluetooth status icon so it switches to `assets/icons/bluetooth/bluetooth_paired.png` whenever Bluetooth is on and the kiosk has at least one paired device in the live snapshot.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-155920.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, ran a `PYTHONPATH=/home/pi/gamehub-console python3` check confirming the status snapshot now includes `bluetooth_paired_devices` and that `bluetooth_icon_path(True, True)` resolves to `bluetooth/bluetooth_paired.png`, restarted the kiosk with `./restart_kiosk.sh`, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-03 16:02:29 +08
- Summary: Corrected the top HUD Bluetooth status behavior so `assets/icons/bluetooth/bluetooth_paired.png` is used only while Bluetooth is on and the kiosk currently has at least one connected device, not merely a paired one.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260403-160229.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, ran a `PYTHONPATH=/home/pi/gamehub-console python3` check confirming `bluetooth_icon_path(True, True)` still resolves to `bluetooth/bluetooth_paired.png` while the HUD update path now keys off `bluetooth_connected_devices`, restarted the kiosk with `./restart_kiosk.sh`, and confirmed fresh `hud_overlay.py`, `gamepad_cursor.py`, and Chromium launcher processes are running in the relaunched session.

## 2026-04-06 11:33:23 +08
- Summary: Added new synthesized kiosk audio cues so settings detail panels now play a single rising chime on open and a single falling chime on close, and the runtime Onboard keyboard now plays two quick ascending tones on open and two quick descending tones on close.
- Files: `hud_overlay.py`, `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-112648.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py`, then ran a `PYTHONPATH=/home/pi/gamehub-console python3` sanity check confirming the new synthesized dropdown-open and OSK-open tone builders generate non-empty audio buffers (`3968` and `4146` bytes).

## 2026-04-06 11:38:18 +08
- Summary: Added a soft single-click OSK key sound so controller `A` selections inside the visible keyboard area and touchscreen taps on the live keyboard now play one key-activation click without affecting non-keyboard interactions.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-113514.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, then ran a `PYTHONPATH=/home/pi/gamehub-console python3` sanity check confirming the new soft-click tone builder returns a non-empty audio buffer (`1588` bytes).

## 2026-04-06 11:46:12 +08
- Summary: Added OSK key-specific activation sounds so `Backspace` now plays a single falling note and `Enter` now plays a single rising chime, while other keyboard keys keep the existing soft click through the shared controller and touchscreen activation path.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-114351.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, then ran a `PYTHONPATH=/home/pi/gamehub-console python3` sanity check confirming `keyboard_sound_kind()` resolves sample pointer positions to `backspace`, `enter`, and `default`, and confirming the new Backspace and Enter synthesized tone buffers are non-empty (`3088` and `3308` bytes).

## 2026-04-06 11:57:18 +08
- Summary: Fixed the immediate-close OSK audio bug by tracking requested keyboard visibility state, canceling stale post-open restore work after a close request, and allowing the close chime to fire only once per actual close transition.
- Files: `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-115250.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/gamepad_cursor.py`, then ran a `PYTHONPATH=/home/pi/gamehub-console python3` sanity check confirming repeated `set_keyboard_target_visible()` calls only mark the first open and close as real transitions while subsequent duplicate requests return `changed=False`.

## 2026-04-06 12:07:11 +08
- Summary: Reduced perceived UI-audio delay and stopped same-family cue overlap by having both kiosk sound players start playback immediately, replace older in-flight processes within the same cue family, and keep a short debounce on rapid OSK keypress sounds.
- Files: `hud_overlay.py`, `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-120404.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py`, then ran `PYTHONPATH=/home/pi/gamehub-console python3` fake-`subprocess.Popen` sanity checks confirming `play_keyboard_open()` followed by `play_keyboard_close()` terminates the first keyboard-transition process before the second starts, and `play_dropdown_open()` followed by `play_dropdown_close()` does the same for settings-dropdown playback.

## 2026-04-06 12:23:19 +08
- Summary: Made the top HUD Wi-Fi, Bluetooth, and volume icons update immediately from runtime Settings changes by pushing local snapshots straight into the dock and by preventing stale background poll results from overwriting newer settings-driven state.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-122007.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, then ran `PYTHONPATH=/home/pi/gamehub-console python3` sanity checks confirming a manual `StatusPoller.set_snapshot()` survives an in-flight stale poll result (`stale_discarded disabled 25`) and that `Hud.handle_status_snapshot_change()` immediately forwards the pushed snapshot into both the poller and status dock (`poller_call 42 False`, `dock_call True`).

## 2026-04-06 12:29:49 +08
- Summary: Extended the HUD toast popup into a live-status notification path so Wi-Fi and Bluetooth connection transitions now raise the same small popup even outside the immediate Settings action callback flow, and battery now raises a one-shot low warning when charge falls to `20%` or lower while not charging.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-122754.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, then ran `PYTHONPATH=/home/pi/gamehub-console python3` sanity checks confirming a single snapshot transition can emit Wi-Fi, Bluetooth, and low-battery popups (`CafeNet Connected`, `Headset Connected`, `Battery Low (19%)`), that repeating the same snapshot does not re-fire those notifications, and that a connected hidden SSID falls back to the `WiFi Connected` popup label.

## 2026-04-06 13:10:27 +08
- Summary: Added the animated `assets/icons/wifi/utility_loading.gif` scan indicator to the expanded Wi-Fi and Bluetooth refresh rows so the GIF plays while a nearby scan is running and disappears again when that refresh completes.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-122754.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, then ran `PYTHONPATH=/home/pi/gamehub-console python3` with Tkinter to confirm `load_status_gif_frames('wifi/utility_loading.gif', 16)` returns `28` frames scaled to `16x16`.

## 2026-04-06 13:25:03 +08
- Summary: Rebuilt `assets/icons/wifi/utility_loading.gif` with a transparent background and a warmer pink-orange loading treatment so the scan indicator sits cleanly on the dark Settings panel without the old white box.
- Files: `assets/icons/wifi/utility_loading.gif`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-132503.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, then ran `python3`/Pillow checks confirming the rebuilt GIF is `16x16` with `21` frames and a transparency index, plus `DISPLAY=:0 python3` Tkinter checks confirming corner pixels in frame `0` report `transparency_get(...) == True` while the center dot remains opaque.

## 2026-04-06 14:31:46 +08
- Summary: Fixed the scan-animation kiosk lockup by stopping the GIF frame callback from queuing a second timer after every render, leaving the refresh indicator with only one pending Tk timer at a time so the Settings overlay stays responsive during Wi-Fi and Bluetooth scans.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-133101.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, then ran `PYTHONPATH=/home/pi/gamehub-console python3` sanity checks confirming one `advance_loading_gif()` tick now advances one frame and requests one render (`advance None 1 1 0`), while repeated `schedule_loading_gif()` calls still leave only a single queued timer (`schedule job-1 [(90, '<lambda>')]`).

## 2026-04-06 14:38:10 +08
- Summary: Removed the Wi-Fi and Bluetooth scan GIF indicator from the runtime Settings overlay and reverted refresh feedback to the existing text-only `Scanning nearby networks...` and `Scanning nearby devices...` row states so scan refresh no longer depends on any GIF animation path.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-143329.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, then ran `grep -nE "utility_loading|loading_gif|scan_loading_visible|schedule_loading_gif|cancel_loading_gif|advance_loading_gif" /home/pi/gamehub-console/hud_overlay.py` and confirmed it returned no matches.

## 2026-04-06 14:58:09 +08
- Summary: Added a dedicated fullscreen boot splash that raises a black screen, fades the existing `assets/images/gbl_logo.png` logo in and back out during kiosk startup, and suppresses that splash during `restart_kiosk.sh` so manual restarts still recycle quickly.
- Files: `boot_splash.py`, `start_kiosk_components.sh`, `restart_kiosk.sh`, `install_gamehub_console.sh`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-145809.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/boot_splash.py`, ran `bash -n /home/pi/gamehub-console/start_kiosk_components.sh && bash -n /home/pi/gamehub-console/restart_kiosk.sh && bash -n /home/pi/gamehub-console/install_gamehub_console.sh`, then ran `PYTHONPATH=/home/pi/gamehub-console python3` sanity checks confirming the splash helper computes `27` eased fade frames from `0.0` to `1.0`, scales the logo to `681x355` for the default `800x480` kiosk screen, and that `restart_kiosk.sh` now execs `env SHOW_BOOT_SPLASH=0 /home/pi/gamehub-console/start_kiosk_components.sh`; also ran a `DISPLAY=:0` Tk check confirming `boot_splash.image_to_photoimage(...)` successfully built a `48x25` `tk.PhotoImage`, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed the live session came back with `unclutter -idle 0 -root`, `hud_overlay.py`, `gamepad_cursor.py`, and `launch_chromium.sh` running while `boot_splash.py` stayed absent on the quick-restart path.

## 2026-04-06 15:15:54 +08
- Summary: Added a repo-managed Plymouth boot theme that uses the shared `assets/images/gbl_logo.png` artwork, redirects visible kernel logs off `tty1`, suppresses the Raspberry Pi rainbow splash, and applies the same splash coverage during shutdown so the kiosk no longer exposes console text on the display.
- Files: `configure_boot_splash.sh`, `files/plymouth-theme/gamehub-console/gamehub-console.plymouth`, `files/plymouth-theme/gamehub-console/gamehub-console.script`, `install_gamehub_console.sh`, `files/knf-kiosk.service`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-151554.md`, `/home/pi/backup/cmdline.txt-20260406-151554`, `/home/pi/backup/config.txt-20260406-151554`.
- Verification: Installed `plymouth` and `plymouth-themes`, ran `bash -n /home/pi/gamehub-console/configure_boot_splash.sh /home/pi/gamehub-console/install_gamehub_console.sh`, ran `sudo bash /home/pi/gamehub-console/configure_boot_splash.sh`, confirmed `plymouth-set-default-theme -l` lists `gamehub-console` after install, confirmed `/boot/firmware/cmdline.txt` now routes the local console to `tty3` with `quiet splash plymouth.ignore-serial-consoles vt.global_cursor_default=0 loglevel=3 udev.log_priority=3 systemd.show_status=false rd.systemd.show_status=false logo.nologo`, confirmed `/boot/firmware/config.txt` now contains `disable_splash=1`, ran `systemctl daemon-reload && systemctl enable knf-kiosk.service`, and confirmed `/etc/systemd/system/display-manager.service` now aliases `knf-kiosk.service`; live visual confirmation of the boot and shutdown splash still requires a reboot on-device.

## 2026-04-06 15:35:32 +08
- Summary: Removed the duplicate post-boot logo by changing `start_kiosk_components.sh` so the X-session `boot_splash.py` path now stays off on normal boots whenever the early Plymouth splash is already configured, leaving the late splash available only as an explicit override or fallback.
- Files: `start_kiosk_components.sh`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-153532.md`.
- Verification: Ran `bash -n /home/pi/gamehub-console/start_kiosk_components.sh /home/pi/gamehub-console/restart_kiosk.sh`, confirmed the startup script now defaults `SHOW_BOOT_SPLASH` to `auto`, confirmed the new `has_early_boot_splash()` path keys off the installed `splash` boot flag and `plymouth-set-default-theme` availability, and confirmed the current machine still has the early splash configured through `/boot/firmware/cmdline.txt`; live on-screen confirmation that the duplicate second splash is gone still requires a reboot.

## 2026-04-06 15:42:01 +08
- Summary: Eliminated the audible lag on Settings and OSK cues by switching both sound players from per-cue `paplay` or `aplay` subprocess launches to a low-latency in-process `pygame.mixer` backend with cached synthesized sounds and family-level channel reuse, while keeping the shell-player path as fallback.
- Files: `hud_overlay.py`, `gamepad_cursor.py`, `install_gamehub_console.sh`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-154201.md`.
- Verification: Installed `python3-pygame`, ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py`, then ran a direct timing probe from `/home/pi/gamehub-console` confirming both sound players now report `backend_name == 'pygame'` and dispatch common cues quickly (`ui_play_scroll_ms 1.49`, `ui_play_slider_ms 0.987`, `kb_key_ms 0.834`, `kb_enter_ms 0.008`); live in-menu and OSK interaction verification still requires the running kiosk session to reload.

## 2026-04-06 15:55:19 +08
- Summary: Backed the UI and OSK sound players away from the regressed Bluetooth `pygame` path by detecting the live Pulse sink, preferring the shell playback backend again on Bluetooth A2DP outputs, and regenerating cue audio at the active Pulse sample rate and channel count so the cues avoid extra server-side format conversion before playback.
- Files: `hud_overlay.py`, `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-155519.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py`, confirmed the current machine reports `Default Sink: bluez_sink.DF_E0_01_31_9D_FE.a2dp_sink` and `Default Sample Specification: s16le 2ch 44100Hz` from `pactl info`, confirmed both sound players now select the shell backend on this machine while inheriting `44100 Hz` stereo synthesis, and confirmed the playback command requests `--latency-msec=8 --process-time-msec=4`; live audible verification in the running kiosk still requires a reload and on-device listening.

## 2026-04-06 16:06:48 +08
- Summary: Reduced the Bluetooth dropdown open-cue lag by deferring the automatic nearby-device scan for a short beat after the Bluetooth detail panel opens, so the dropdown-open cue gets a chance to play before discovery traffic competes with Bluetooth A2DP audio on the shared radio.
- Files: `hud_overlay.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-160648.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py`, confirmed `open_bluetooth_detail()` now schedules the initial refresh instead of launching it inline, confirmed explicit `Refresh nearby devices` actions still call `request_list_refresh(BLUETOOTH_ITEM_KEY, force=True)` immediately, and confirmed the pending delayed refresh is canceled when the panel closes, a manual refresh starts, or a Bluetooth action completes; live audible verification still requires the running kiosk session to reload and be tested while the Bluetooth A2DP sink is active.

## 2026-04-06 16:33:18 +0800
- Summary: Replaced the unfinished per-cue audio path with a shared persistent PCM streamer so HUD and OSK cues now stay on one live low-latency `pacat` or `aplay` connection, emit in small real-time chunks, and can preempt older same-family cues without piling up audible queue delay.
- Files: `audio_output.py`, `hud_overlay.py`, `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-162820.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/audio_output.py /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py`, ran a direct `PersistentPcmAudioOutput` sanity probe from `/home/pi/gamehub-console` confirming the live machine resolves to `44100 Hz` stereo on `bluez_sink.DF_E0_01_31_9D_FE.a2dp_sink` with backend `pacat`, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed the fresh live session contains `python3 /home/pi/gamehub-console/hud_overlay.py`, `python3 /home/pi/gamehub-console/gamepad_cursor.py`, and `/bin/bash /home/pi/gamehub-console/launch_chromium.sh`; final audible confirmation still requires on-device interaction after the restart.

## 2026-04-06 16:44:07 +0800
- Summary: Tightened the kiosk cue policy by putting the HUD and OSK on one shared monophonic cue bus, making every new UI cue interrupt stale queued cues instead of stacking, and raising the navigation and keypress repeat gates to match the cue lengths so rapid interactions sound cleaner and more deliberate.
- Files: `audio_output.py`, `hud_overlay.py`, `gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-164407.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/audio_output.py /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py`, ran `PYTHONPATH=/home/pi/gamehub-console python3` sanity checks confirming `UiSoundPlayer().output is KeyboardSoundPlayer().output`, confirming the shared output still resolves to backend `pacat` at `44100 Hz` stereo, and confirming a rapid `play_scroll()`, `play_slider()`, `play_keyboard_key_click()` sequence leaves only one queued voice on the shared bus instead of stacking multiple queued cues; live audible confirmation still requires the running kiosk session to reload and be tested on-device.

## 2026-04-06 16:55:39 +0800
- Summary: Fixed the slider overlap bug inside the shared cue mixer by giving replacement cues generation-based cancellation, so an earlier panel-open or slider sound that was already captured for mixing can no longer be re-added over a newer slider tick on the next chunk.
- Files: `audio_output.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-165539.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/audio_output.py /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/gamepad_cursor.py`, then ran a direct `PYTHONPATH=/home/pi/gamehub-console python3` mixer probe with a no-backend `DummyOutput` confirming an old `settings-dropdown` voice reports valid before replacement, becomes invalid immediately after a `slider` replacement cue arrives, and leaves only `['slider']` queued after the replacement instead of re-adding the older cue.

## 2026-04-06 17:19:34 +0800
- Summary: Added a visible fade-in to the repo-managed Plymouth logo theme and changed normal boots to use a seamless X-session handoff overlay that starts on the same fully visible logo frame and only fades that logo back out, while keeping the full fallback X-session splash for systems without Plymouth and still suppressing splash playback on `restart_kiosk.sh`.
- Files: `boot_splash.py`, `start_kiosk_components.sh`, `files/plymouth-theme/gamehub-console/gamehub-console.script`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-171934.md`.
- Verification: Ran `bash -n /home/pi/gamehub-console/start_kiosk_components.sh /home/pi/gamehub-console/restart_kiosk.sh /home/pi/gamehub-console/configure_boot_splash.sh /home/pi/gamehub-console/install_gamehub_console.sh`, ran `python3 -m py_compile /home/pi/gamehub-console/boot_splash.py`, ran `PYTHONPATH=/home/pi/gamehub-console python3` sanity checks confirming `BOOT_SPLASH_MODE` resolves to `handoff` and `full` correctly and that the splash helper still computes `27` eased frames from `0.0` to `1.0`, ran `sudo bash /home/pi/gamehub-console/configure_boot_splash.sh`, confirmed `/usr/share/plymouth/themes/gamehub-console/gamehub-console.script` now contains the new fade-in logic, confirmed `/boot/firmware/cmdline.txt` still contains `quiet splash plymouth.ignore-serial-consoles ... logo.nologo` and `/boot/firmware/config.txt` still contains `disable_splash=1`, confirmed `SHOW_BOOT_SPLASH=auto` now resolves to `handoff` on this machine, then ran `bash /home/pi/gamehub-console/restart_kiosk.sh` and confirmed the live session contains `unclutter -idle 0 -root`, `python3 /home/pi/gamehub-console/hud_overlay.py`, `python3 /home/pi/gamehub-console/gamepad_cursor.py`, and `/bin/bash /home/pi/gamehub-console/launch_chromium.sh` while `boot_splash.py` stays absent on the quick-restart path; final visual confirmation of the Plymouth fade-in and the normal-boot handoff fade-out still requires a reboot on-device.

## 2026-04-06 17:30:16 +0800
- Summary: Removed the extra post-boot X splash from the default startup path so Plymouth-backed boots now show only the first boot splash, while keeping the fallback and explicit override splash modes available for systems that do not have the early splash path.
- Files: `start_kiosk_components.sh`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260406-173016.md`.
- Verification: Ran `bash -n /home/pi/gamehub-console/start_kiosk_components.sh /home/pi/gamehub-console/restart_kiosk.sh`, confirmed `/usr/sbin/plymouth-set-default-theme` is installed, confirmed `/boot/firmware/cmdline.txt` still contains the `quiet splash` Plymouth boot flags, and confirmed the `SHOW_BOOT_SPLASH=auto` branch in `start_kiosk_components.sh` now resolves to `none` when the early Plymouth splash is present; final on-screen confirmation that the second splash is gone still requires a reboot on-device.

## 2026-04-07 11:20:17 +0800
- Summary: Removed the temporary `Splash` test action from the live Settings overlay and disabled `boot_splash.py` audio playback for now while keeping the visual splash flow unchanged.
- Files: `hud_overlay.py`, `boot_splash.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/backup/AGENTS-20260407-112017.md`.
- Verification: Ran `python3 -m py_compile /home/pi/gamehub-console/hud_overlay.py /home/pi/gamehub-console/boot_splash.py`, confirmed the live settings item list now contains only `Volume`, `WiFi`, `Bluetooth`, `Brightness`, `Restart Kiosk`, and `Shutdown`, and confirmed `BootSplash` now skips `SplashJinglePlayer` construction unless `SPLASH_AUDIO_ENABLED` is re-enabled; live on-device confirmation still requires opening Settings and running a normal boot or X-session splash path.

## 2026-04-07 16:37:11 +0800
- Summary: Promoted `/home/pi/release` to the canonical kiosk workspace by moving the live kiosk trees there, leaving compatibility symlinks at the legacy `/home/pi/...` paths, making the repo runtime scripts resolve their own real location cleanly, and updating the installed service, cron, sudoers, and documentation paths to match the new release-root layout.
- Files: `common.py`, `gamepad_cursor.py`, `hud_overlay.py`, `backup_rollback_zip.sh`, `configure_boot_splash.sh`, `display_mode.sh`, `install_gamehub_console.sh`, `launch_chromium.sh`, `restart_kiosk.sh`, `start_kiosk_components.sh`, `console.env`, `README.md`, `raspi-config-checklist.txt`, `files/knf-kiosk.service`, `files/gamehub-console-backup.cron`, `files/gamehub-console-sudoers`, `files/openbox/autostart`, `files/gamepad_cursor.py`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/release/`, `/home/pi/release/.config/openbox/autostart`, `/etc/systemd/system/knf-kiosk.service`, `/etc/cron.d/gamehub-console-backup`, `/etc/sudoers.d/gamehub-console`, `/home/pi/release/backup/AGENTS-20260407-163023.md`.
- Verification: Synced the live `/home/pi/gamehub-console`, `.config`, `.local`, `.icons`, `.xinitrc`, `backup`, and `kiosk-backup-latest.zip` content into `/home/pi/release`, replaced the old home-root copies with symlinks back to `/home/pi/release`, refreshed `/home/pi/release/.xinitrc` and `/home/pi/release/.config/openbox/autostart` from the updated repo templates, installed the updated system files to `/etc/systemd/system/knf-kiosk.service`, `/etc/cron.d/gamehub-console-backup`, and `/etc/sudoers.d/gamehub-console`, ran `sudo visudo -c -f /etc/sudoers.d/gamehub-console`, ran `sudo systemctl daemon-reload`, ran `python3 -m py_compile /home/pi/release/gamehub-console/common.py /home/pi/release/gamehub-console/gamepad_cursor.py /home/pi/release/gamehub-console/hud_overlay.py /home/pi/release/gamehub-console/boot_splash.py /home/pi/release/gamehub-console/settings_gui.py`, ran `bash -n /home/pi/release/gamehub-console/backup_rollback_zip.sh /home/pi/release/gamehub-console/configure_boot_splash.sh /home/pi/release/gamehub-console/display_mode.sh /home/pi/release/gamehub-console/install_gamehub_console.sh /home/pi/release/gamehub-console/launch_chromium.sh /home/pi/release/gamehub-console/restart_kiosk.sh /home/pi/release/gamehub-console/start_kiosk_components.sh`, ran `bash /home/pi/release/gamehub-console/backup_rollback_zip.sh` and confirmed it built `/home/pi/release/backup/console_backup_20260407_163811.zip`, confirmed the legacy `/home/pi/...` entry points are now symlinks into `/home/pi/release`, confirmed the repo no longer contains non-historical hard-coded `/home/pi/gamehub-console`, `/home/pi/.xinitrc`, or `/home/pi/backup` runtime paths outside the intentional compatibility notes in `AGENTS.md`, and confirmed the installed system files now reference `/home/pi/release`.

## 2026-04-07 17:01:23 +0800
- Summary: Promoted `/home/pi/Xiphias` to the canonical kiosk workspace, retired the intermediate `/home/pi/release` root, updated the repo docs/config/templates plus installed system files to `Xiphias`, moved the live kiosk tree there, restarted the kiosk service into the new root, and removed the obsolete `release` layout after the relaunched session was confirmed healthy.
- Files: `README.md`, `console.env`, `raspi-config-checklist.txt`, `files/knf-kiosk.service`, `files/gamehub-console-backup.cron`, `files/gamehub-console-sudoers`, `files/openbox/autostart`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/Xiphias/`, `/home/pi/.config`, `/home/pi/.icons`, `/home/pi/.local`, `/home/pi/.xinitrc`, `/home/pi/gamehub-console`, `/home/pi/backup`, `/home/pi/kiosk-backup-latest.zip`, `/etc/systemd/system/knf-kiosk.service`, `/etc/cron.d/gamehub-console-backup`, `/etc/sudoers.d/gamehub-console`, `/home/pi/Xiphias/backup/AGENTS-20260407-165415.md`.
- Verification: Created the pre-cutover `AGENTS-20260407-165415.md` backup before editing `AGENTS.md` and carried it forward to `/home/pi/Xiphias/backup/AGENTS-20260407-165415.md`, updated the repo files so the canonical path is now `/home/pi/Xiphias`, synced `/home/pi/release/` into `/home/pi/Xiphias/`, refreshed `/home/pi/Xiphias/.xinitrc` and `/home/pi/Xiphias/.config/openbox/autostart` from the updated repo templates, installed the new Xiphias-root service/cron/sudoers files to `/etc/systemd/system/knf-kiosk.service`, `/etc/cron.d/gamehub-console-backup`, and `/etc/sudoers.d/gamehub-console`, ran `sudo visudo -c -f /etc/sudoers.d/gamehub-console`, ran `sudo systemctl daemon-reload`, rotated the `/home/pi/.config`, `/home/pi/.icons`, `/home/pi/.local`, `/home/pi/.xinitrc`, `/home/pi/gamehub-console`, `/home/pi/backup`, and `/home/pi/kiosk-backup-latest.zip` symlinks to `/home/pi/Xiphias`, ran `sudo systemctl restart knf-kiosk.service`, cleared the stale release-rooted `startx` and Chromium session so systemd could finish the restart, confirmed the relaunched live session now uses `/home/pi/Xiphias/.xinitrc`, `/home/pi/Xiphias/gamehub-console/hud_overlay.py`, `/home/pi/Xiphias/gamehub-console/gamepad_cursor.py`, `/home/pi/Xiphias/gamehub-console/launch_chromium.sh`, and Chromium `--app=file:///home/pi/Xiphias/gamehub-console/kiosk-wrapper.html#https://handheld.knfstudios.com/?mode=handheld`, ran `python3 -m py_compile /home/pi/Xiphias/gamehub-console/common.py /home/pi/Xiphias/gamehub-console/gamepad_cursor.py /home/pi/Xiphias/gamehub-console/hud_overlay.py /home/pi/Xiphias/gamehub-console/boot_splash.py /home/pi/Xiphias/gamehub-console/settings_gui.py`, ran `bash -n /home/pi/Xiphias/gamehub-console/backup_rollback_zip.sh /home/pi/Xiphias/gamehub-console/configure_boot_splash.sh /home/pi/Xiphias/gamehub-console/display_mode.sh /home/pi/Xiphias/gamehub-console/install_gamehub_console.sh /home/pi/Xiphias/gamehub-console/launch_chromium.sh /home/pi/Xiphias/gamehub-console/restart_kiosk.sh /home/pi/Xiphias/gamehub-console/start_kiosk_components.sh`, ran `bash /home/pi/Xiphias/gamehub-console/backup_rollback_zip.sh` and confirmed it built `/home/pi/Xiphias/backup/console_backup_20260407_170122.zip`, confirmed `/etc/systemd/system/knf-kiosk.service`, `/etc/cron.d/gamehub-console-backup`, `/etc/sudoers.d/gamehub-console`, and `/home/pi/Xiphias/.config/openbox/autostart` now reference `/home/pi/Xiphias` and not `/home/pi/release`, then removed the temporary `/home/pi/release` compatibility link plus the retired pre-cutover `/home/pi/.release-retired-20260407-165415` tree so the old release-rooted layout is no longer present.

## 2026-04-09 09:51:52 +0800
- Summary: Added a GitHub-based OTA pull script for the release checkout, documented `/home/pi/Xiphias/release` as the Git-backed staging mirror instead of the live runtime root, and documented the pull-and-deploy OTA flow for private GitHub releases while preserving local device state.
- Files: `ota_git_update.sh`, `README.md`, `AGENTS.md`, `timestamp-console.md`, `/home/pi/Xiphias/backup/AGENTS-20260409-095152.md`.
- Verification: Ran `bash -n /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh`, ran `bash /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh --help`, confirmed the new script resolves the live and release roots relative to its own path, preserves `console.env`, `logs/`, and `__pycache__/` during managed-path syncs, and supports `--apply-system-files`, `--skip-backup`, and `--no-restart`; also probed the configured GitHub OTA settings and confirmed the current token does not yet have usable read access to the private `miuni-ta/Xiphias` repo, so a corrected read-capable token or deploy key is still required before a live OTA pull can succeed.

## 2026-04-09 10:26:33 +0800
- Summary: Converted `/home/pi/Xiphias` into the real git worktree for `miuni-ta/Xiphias`, configured SSH push and pull on this machine with a writable repo deploy key, confirmed `console.env` stays ignored, and updated the OTA docs to reflect that `release/` is the tracked deploy payload inside the main repo rather than a separate git mirror.
- Files: `.gitignore`, `/home/pi/.ssh/config`, `/home/pi/.ssh/id_ed25519_xiphias_github`, `/home/pi/.ssh/id_ed25519_xiphias_github.pub`, `release/gamehub-console/AGENTS.md`, `release/gamehub-console/README.md`, `release/gamehub-console/timestamp-console.md`, `/home/pi/Xiphias/backup/AGENTS-20260409-102633.md`.
- Verification: Confirmed `.gitignore` contains `console.env`, `*.log`, `__pycache__/`, `*.pyc`, `backup/`, and `logs/`; confirmed `git -C /home/pi/Xiphias check-ignore -v release/gamehub-console/console.env` resolves through the repo `.gitignore`; added the repo deploy key through the GitHub API with `read_only:false`; confirmed `ssh -o BatchMode=yes -T github-xiphias` authenticates to `miuni-ta/Xiphias`; confirmed `git -C /home/pi/Xiphias ls-remote --heads origin` returns `master`; confirmed `git push --dry-run origin HEAD:refs/heads/__codex_ssh_push_probe__` succeeds from a temporary repo over SSH; and confirmed the local repo identity is set to `Ahmad Luqman <ahmadluqman@todak.com>`. No OTA deploy was run in this step.

## 2026-04-09 10:54:15 +0800
- Summary: Added a live `Update Software` row to the Settings overlay and standalone settings preview, showing the deployed version from `/home/pi/Xiphias/version.txt` and triggering the git-backed OTA flow from the menu before restarting the kiosk after a successful update. Also aligned the OTA helper and repo guidance with the current Xiphias-root git worktree layout.
- Files: `release/gamehub-console/common.py`, `release/gamehub-console/hud_overlay.py`, `release/gamehub-console/settings_gui.py`, `release/gamehub-console/ota_git_update.sh`, `release/gamehub-console/AGENTS.md`, `release/gamehub-console/timestamp-console.md`, `/home/pi/Xiphias/backup/AGENTS-20260409-104706.md`.
- Verification: Ran `python3 -m py_compile /home/pi/Xiphias/release/gamehub-console/common.py /home/pi/Xiphias/release/gamehub-console/hud_overlay.py /home/pi/Xiphias/release/gamehub-console/settings_gui.py /home/pi/Xiphias/gamehub-console/common.py /home/pi/Xiphias/gamehub-console/hud_overlay.py /home/pi/Xiphias/gamehub-console/settings_gui.py`; ran `bash -n /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh && bash -n /home/pi/Xiphias/gamehub-console/ota_git_update.sh`; and confirmed the synced live copies match the tracked release files with `cmp -s` for `common.py`, `hud_overlay.py`, `settings_gui.py`, and `ota_git_update.sh`. No live OTA pull was executed in this step.

## 2026-04-09 11:17:36 +0800
- Summary: Changed the Settings OTA row from `Update Software` to `Check for Updates`, so the kiosk now checks GitHub first and only opens the install confirmation dropdown when remote changes are available. Also added `ota_git_update.sh --check-only` for the menu-side repo check and updated the kiosk guidance to match the new two-step flow.
- Files: `release/gamehub-console/hud_overlay.py`, `release/gamehub-console/settings_gui.py`, `release/gamehub-console/ota_git_update.sh`, `release/gamehub-console/AGENTS.md`, `release/gamehub-console/timestamp-console.md`, `/home/pi/Xiphias/backup/AGENTS-20260409-111722.md`.
- Verification: Ran `python3 -m py_compile /home/pi/Xiphias/release/gamehub-console/hud_overlay.py /home/pi/Xiphias/release/gamehub-console/settings_gui.py /home/pi/Xiphias/gamehub-console/hud_overlay.py /home/pi/Xiphias/gamehub-console/settings_gui.py`; ran `bash -n /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh && bash -n /home/pi/Xiphias/gamehub-console/ota_git_update.sh`; and confirmed the synced live copies match the tracked release files with `cmp -s` for `hud_overlay.py`, `settings_gui.py`, and `ota_git_update.sh`. No live update check or OTA pull was executed in this step.

## 2026-04-09 12:23:56 +0800
- Summary: Fixed the Settings `Check for Updates` flow so repo checks no longer fail on a dirty local git worktree, no-update results now show `Updated to latest version`, and OTA deploys fall back to a temporary GitHub checkout when the local worktree cannot be fast-forwarded safely.
- Files: `release/gamehub-console/hud_overlay.py`, `release/gamehub-console/ota_git_update.sh`, `release/gamehub-console/AGENTS.md`, `release/gamehub-console/timestamp-console.md`, `/home/pi/Xiphias/backup/AGENTS-20260409-121905.md`.
- Verification: Ran `python3 -m py_compile /home/pi/Xiphias/release/gamehub-console/hud_overlay.py /home/pi/Xiphias/gamehub-console/hud_overlay.py`; ran `bash -n /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh && bash -n /home/pi/Xiphias/gamehub-console/ota_git_update.sh`; and confirmed the synced live copies match the tracked release files with `cmp -s` for `hud_overlay.py` and `ota_git_update.sh`. No live update check or OTA pull was executed in this step.

## 2026-04-09 12:25:12 +0800
- Summary: Corrected the `--check-only` control flow so an up-to-date local worktree no longer falls through into the clone-based diff path. The live repo-check probe now returns `CHECK_STATUS=up-to-date` with exit code `0`, which lets the Settings menu show the new `Updated to latest version` message instead of a false update-available state.
- Files: `release/gamehub-console/ota_git_update.sh`, `release/gamehub-console/timestamp-console.md`.
- Verification: Ran `bash -n /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh && bash -n /home/pi/Xiphias/gamehub-console/ota_git_update.sh`; ran `bash /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh --check-only` and confirmed it returned `CHECK_STATUS=up-to-date`, `CHECK_CURRENT_VERSION=1.0.0`, `CHECK_REMOTE_VERSION=1.0.0`, and exit code `0`; and confirmed the synced live OTA script matches the tracked release copy with `cmp -s`.

## 2026-04-09 13:18:42 +0800
- Summary: Fixed the blank-screen OTA restart path by making the kiosk restart scripts invoke their child shell scripts through `bash` instead of relying on execute bits, updated the Settings OTA flow so repo-only remote commits return `Updated to latest version` without restarting, and hardened the git OTA path so a divergent local `/home/pi/Xiphias` worktree is never overwritten by a temporary remote checkout when evaluating or applying updates.
- Files: `release/gamehub-console/restart_kiosk.sh`, `release/gamehub-console/start_kiosk_components.sh`, `release/gamehub-console/hud_overlay.py`, `release/gamehub-console/ota_git_update.sh`, `release/gamehub-console/AGENTS.md`, `release/gamehub-console/timestamp-console.md`, `/home/pi/Xiphias/backup/AGENTS-20260409-131600.md`.
- Verification: Ran `python3 -m py_compile /home/pi/Xiphias/release/gamehub-console/hud_overlay.py /home/pi/Xiphias/gamehub-console/hud_overlay.py`; ran `bash -n /home/pi/Xiphias/release/gamehub-console/restart_kiosk.sh /home/pi/Xiphias/release/gamehub-console/start_kiosk_components.sh /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh /home/pi/Xiphias/gamehub-console/restart_kiosk.sh /home/pi/Xiphias/gamehub-console/start_kiosk_components.sh /home/pi/Xiphias/gamehub-console/ota_git_update.sh`; confirmed the synced live copies match the tracked release files with `cmp -s` for `restart_kiosk.sh`, `start_kiosk_components.sh`, `hud_overlay.py`, and `ota_git_update.sh`; ran `bash /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh --no-restart` against the placeholder-only GitHub change and confirmed it returned `OTA_STATUS=no-live-change`, `OTA_CURRENT_VERSION=1.0.0`, `OTA_REMOTE_VERSION=1.0.0`, and exit code `0`; then ran `bash /home/pi/Xiphias/release/gamehub-console/ota_git_update.sh --check-only` and confirmed it returned `CHECK_STATUS=up-to-date`, `CHECK_CURRENT_VERSION=1.0.0`, `CHECK_REMOTE_VERSION=1.0.0`, and exit code `0`.

## 2026-04-09 13:36:40 +0800
- Summary: Fixed the remaining blank-screen kiosk startup path by making the Openbox autostart launcher call `start_kiosk_components.sh` through `bash`, and restored executable bits on the tracked kiosk shell scripts so Openbox restarts, OTA restarts, and direct launches all use a consistent executable startup chain.
- Files: `release/.config/openbox/autostart`, `release/gamehub-console/files/openbox/autostart`, `release/gamehub-console/launch_chromium.sh`, `release/gamehub-console/restart_kiosk.sh`, `release/gamehub-console/start_kiosk_components.sh`, `release/gamehub-console/timestamp-console.md`.
- Verification: Confirmed the live blank-screen state had no `hud_overlay.py`, `gamepad_cursor.py`, or Chromium processes while `/home/pi/Xiphias/.config/openbox/autostart` still launched `/home/pi/Xiphias/gamehub-console/start_kiosk_components.sh` directly; patched the Openbox autostart files to run `bash /home/pi/Xiphias/gamehub-console/start_kiosk_components.sh`; restored executable bits for `launch_chromium.sh`, `restart_kiosk.sh`, and `start_kiosk_components.sh` in both the live and tracked trees; restarted `knf-kiosk.service`; force-terminated the stale pre-fix `startx` session so the pending systemd restart could complete; then confirmed the new `13:36 +08` kiosk session came back active with fresh `openbox`, `python3 /home/pi/Xiphias/gamehub-console/hud_overlay.py`, `python3 /home/pi/Xiphias/gamehub-console/gamepad_cursor.py`, `bash /home/pi/Xiphias/gamehub-console/launch_chromium.sh`, Chromium, `unclutter -idle 0 -root`, and `python3 /home/pi/Xiphias/gamehub-console/boot_splash.py` processes.

## 2026-04-09 13:47:18 +0800
- Summary: Fixed the OTA updater so repo-only GitHub changes still track the true latest `origin/master` state instead of being marked handled without syncing the repo payload. The updater now expands a shallow clean local `/home/pi/Xiphias` git checkout before attempting the fast-forward pull, non-git deployments now sync the full `release/` payload into the local release staging tree even when there is no kiosk-managed live change to deploy or restart for, and the OTA helper now resolves the Xiphias workspace root correctly whether it is launched from `release/gamehub-console` or the synced live `gamehub-console` copy.
- Files: `release/gamehub-console/ota_git_update.sh`, `release/gamehub-console/timestamp-console.md`.
- Verification: Confirmed `origin/master` contains a newer `release/placeholder.txt` body than the local `/home/pi/Xiphias/release/placeholder.txt`; traced the old updater path and confirmed it exited on `OTA_STATUS=no-live-change` before syncing `release/`; patched the updater to unshallow clean local worktrees before `git pull --ff-only`, added full-release staging sync for clone-based non-git deployments, and kept the existing no-restart behavior for repo-only commits that do not touch live kiosk-managed paths.

## 2026-04-09 14:28:11 +0800
- Summary: Tightened the Settings `Install Update` flow so it now fetches `origin` and then pulls the latest `OTA_BRANCH` into the real `/home/pi/Xiphias` git worktree before deploying any update. On this machine, installs no longer silently fall back to a temporary clone when `/home/pi/Xiphias` exists as the main repo; instead they require that worktree to be clean and on the expected branch so the local repo truly matches the latest `miuni-ta/Xiphias` state first. The same install success path now always schedules a kiosk restart.
- Files: `release/gamehub-console/hud_overlay.py`, `release/gamehub-console/ota_git_update.sh`, `release/gamehub-console/timestamp-console.md`.
- Verification: Confirmed the Settings menu install command still uses the release-copy OTA helper, updated the HUD success path so every successful install schedules `Restart Kiosk`, confirmed `prepare_worktree_source_root()` now runs `git fetch origin ${OTA_BRANCH}` before `git pull --ff-only origin ${OTA_BRANCH}`, changed the install source-selection path so a present `/home/pi/Xiphias` worktree now fails with a clear message instead of switching to a temporary GitHub clone when that local repo is dirty or on the wrong branch, and restarted the live kiosk after syncing the updated HUD and OTA files into `/home/pi/Xiphias/gamehub-console`.
