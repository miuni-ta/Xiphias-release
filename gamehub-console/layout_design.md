# GameHub OS — UI Design & Layout Prompt for Codex CLI

## Project Context
Replace the existing UI layer of this kiosk web app with the design system described below.
The app runs fullscreen at **800×480px** in a Chromium kiosk on Raspberry Pi 5 (no desktop, no mouse, gamepad-only input). Do **not** change any backend logic, routing, or data-fetching. Only restyle and restructure the HTML/CSS/JS for the frontend UI layer.

---

## 1. Canvas & Reset

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  width: 800px;
  height: 480px;
  overflow: hidden;
  background: #0d0d0f;
  color: #ffffff;
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  cursor: none;
  user-select: none;
}

#app {
  width: 800px;
  height: 480px;
  display: flex;
  flex-direction: column;
  position: relative;
}
```

**Fonts — load from Google Fonts:**
- `Inter` weights 400, 500, 600, 700, 800 — all UI text
- `Share Tech Mono` — clock and numeric readouts only

---

## 2. Design Tokens (CSS Variables)

Declare on `:root`. Use everywhere — no hardcoded hex values in component CSS.

```css
:root {
  --bg:          #0d0d0f;
  --bg-surface:  #141416;
  --bg-card:     #181820;
  --bg-overlay:  #1c1c22;

  --text:        #ffffff;
  --text-muted:  #7a7d8a;
  --text-dim:    #3a3d4a;

  --accent:      #22c55e;
  --accent-glow: rgba(34, 197, 94, 0.30);
  --accent-dim:  rgba(34, 197, 94, 0.10);

  --star:        #f59e0b;
  --blue:        #3b82f6;
  --red:         #ef4444;

  --border:        rgba(255, 255, 255, 0.07);
  --border-focus:  rgba(34, 197, 94, 0.50);

  --radius: 12px;
  --gap:    13px;
  --pad:    20px;
}
```

---

## 3. Page Structure

The root `#app` is a vertical flex column that fills exactly 800×480 with no scroll:

```
┌─────────────────────────────────┐  36px  — Status Bar
├─────────────────────────────────┤  48px  — Page Header
├─────────────────────────────────┤  flex:1 — Game Grid
└─────────────────────────────────┘  38px  — Hint Bar
                              Total: 480px
```

---

## 4. Status Bar — 36px

**Container:**
```css
height: 36px;
display: flex; align-items: center; justify-content: space-between;
padding: 0 18px;
background: rgba(10, 10, 12, 0.95);
border-bottom: 1px solid var(--border);
flex-shrink: 0;
```

**Left — Clock:**
Font: `Share Tech Mono`, 13px, `letter-spacing: 0.05em`.
Displays `HH:MM` in 24-hour format, updated every second via `setInterval`.

**Right — Three system chips (flex row, gap 14px):**
Each chip: `display: flex; align-items: center; gap: 5px; font-size: 11px;`

**Chip 1 — Bluetooth:**
SVG bluetooth icon (14×14px stroke) + text label showing connected device name (e.g. "Gamepad"). Color `var(--text)` when connected, `var(--text-dim)` when off.

**Chip 2 — WiFi:**
Four ascending bars + text label showing active SSID name.
```css
/* Bar group */
display: flex; align-items: flex-end; gap: 2px; height: 12px;
/* Each bar */
width: 3px; border-radius: 1px;
/* Heights: */ 4px · 7px · 10px · 13px
/* Connected: */ background: white;
/* Disconnected: */ background: var(--text-dim);
```

**Chip 3 — Battery:**
Pill outline 24×12px (border: 1.5px solid rgba(255,255,255,0.5), border-radius: 3px, padding: 1.5px).
Right-side nub via `::after` (position: absolute; right: -4px; width: 2.5px; height: 6px).
Inner fill bar width matches battery percentage. Label: `font-size: 11.5px; font-weight: 500;`

---

## 5. Page Header — 48px

```css
height: 48px;
display: flex; align-items: center; justify-content: space-between;
padding: 0 var(--pad);
flex-shrink: 0;
```

**Left — Title group (flex row, gap 10px):**
- Bookshelf/library SVG icon, 24×24px, stroke white, stroke-width 2
- Title text: `font-size: 22px; font-weight: 800; letter-spacing: -0.01em;`

**Right — Filter chips (flex row, gap 6px):**
```css
/* Default chip */
padding: 3px 10px; border-radius: 20px;
background: rgba(255,255,255,0.06);
border: 1px solid var(--border);
font-size: 11px; font-weight: 500; color: var(--text-muted);

/* Active chip */
background: var(--accent-dim);
border-color: var(--accent);
color: var(--accent);
```
Chip labels: "All", "GDevelop5", "MakeCode", "Free"

---

## 6. Game Grid — flex: 1

```css
/* Wrapper */
flex: 1; overflow: hidden; padding: 4px var(--pad) 0;

/* Grid */
display: grid;
grid-template-columns: repeat(3, 1fr);
gap: var(--gap);
```

Cards fill the available height. The bottom row is intentionally allowed to clip — signalling scrollability.

---

## 7. Game Card

**HTML structure:**
```html
<div class="game-card" data-idx="N">
  <div class="card-thumb">
    <img src="..." alt="..." loading="lazy">
  </div>
  <div class="card-badge free">FREE</div>
  <div class="card-engine">GDevelop5</div>
  <div class="card-info">
    <div class="card-text">
      <div class="card-name">Title</div>
      <div class="card-dev">by developer</div>
    </div>
    <div class="card-rating">
      <span class="star">★</span>
      <span class="score">4.5</span>
    </div>
  </div>
</div>
```

**Base:**
```css
.game-card {
  border-radius: var(--radius);
  overflow: hidden;
  position: relative;
  background: var(--bg-card);
  aspect-ratio: 3 / 2.15;
  border: 2.5px solid transparent;
  cursor: none;
  transition: transform 0.14s ease, filter 0.14s ease,
              border-color 0.14s ease, box-shadow 0.14s ease;
}
```

**Unfocused (all cards not currently selected):**
```css
.game-card:not(.focused) { filter: brightness(0.65); }
```

**Focused (single active card):**
```css
.game-card.focused {
  border-color: var(--accent);
  box-shadow:
    0 0 0 2px var(--accent-glow),
    0 0 22px rgba(34, 197, 94, 0.22),
    0 6px 20px rgba(0, 0, 0, 0.50);
  transform: scale(1.022);
  z-index: 2;
  filter: brightness(1);
}
```

**Thumbnail:**
```css
.card-thumb {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  background: #1a1a2a; /* placeholder color while loading */
}
.card-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
```

**Info gradient overlay (bottom of card):**
```css
.card-info {
  position: absolute; left: 0; right: 0; bottom: 0;
  padding: 28px 11px 9px;
  background: linear-gradient(
    to top,
    rgba(0,0,0,0.92)  0%,
    rgba(0,0,0,0.55) 55%,
    transparent      100%
  );
  display: flex; align-items: flex-end; justify-content: space-between;
}
.card-name {
  font-size: 13.5px; font-weight: 700; color: white;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  text-shadow: 0 1px 4px rgba(0,0,0,0.7); margin-bottom: 2px;
}
.card-dev { font-size: 10.5px; color: rgba(200,205,215,0.65); }
```

**Badge (absolute, top-left):**
```css
.card-badge {
  position: absolute; top: 8px; left: 8px;
  font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px;
}
.card-badge.free { background: rgba(34,197,94,0.85); color: #000; }
.card-badge.paid { background: rgba(245,158,11,0.90); color: #000; }
```

**Engine tag (absolute, top-right):**
```css
.card-engine {
  position: absolute; top: 8px; right: 8px;
  font-size: 9px; font-weight: 600; padding: 2px 6px; border-radius: 4px;
  background: rgba(0,0,0,0.55); color: rgba(255,255,255,0.65);
  border: 1px solid rgba(255,255,255,0.10);
}
```

**Rating (right side of card-info):**
```css
.card-rating { display: flex; align-items: center; gap: 3px; flex-shrink: 0; margin-left: 8px; }
.card-rating .star  { font-size: 12px; color: var(--star); }
.card-rating .score { font-size: 12px; font-weight: 600; color: white; }
```

**Staggered entry animation:**
```css
@keyframes cardIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0);   }
}
.game-card                { animation: cardIn 0.3s ease both; }
.game-card:nth-child(1)   { animation-delay: 0.04s; }
.game-card:nth-child(2)   { animation-delay: 0.09s; }
.game-card:nth-child(3)   { animation-delay: 0.14s; }
.game-card:nth-child(4)   { animation-delay: 0.19s; }
.game-card:nth-child(5)   { animation-delay: 0.24s; }
.game-card:nth-child(6)   { animation-delay: 0.29s; }
```

---

## 8. Hint Bar — 38px

```css
.hint-bar {
  height: 38px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px;
  border-top: 1px solid var(--border);
  background: rgba(8, 8, 10, 0.95);
}
```

**Each hint group:** `display: flex; align-items: center; gap: 20px;`
**Each hint:** `display: flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 500; color: rgba(200,205,215,0.8);`

**Button glyphs:**
```css
/* Circle (A / B) */
width: 20px; height: 20px; border-radius: 50%;
display: inline-flex; align-items: center; justify-content: center;
font-size: 9px; font-weight: 800; flex-shrink: 0;
/* A */ background: #4ade80; color: #000;
/* B */ background: #f87171; color: #fff;

/* START badge */
padding: 0 7px; height: 18px; border-radius: 4px;
background: rgba(255,255,255,0.14);
font-size: 8.5px; letter-spacing: 0.06em; color: white;

/* D-pad box */
width: 20px; height: 20px; border-radius: 4px;
background: rgba(255,255,255,0.14);
/* contains a crosshair SVG 13×13px */
```

**Vertical separator between groups:** `width: 1px; height: 18px; background: var(--border);`

**Hint labels (left to right):** `Move Cursor` · `Click / Select` · `Back` · `Settings`

**Right side:** site attribution text, `font-size: 10.5px; color: var(--text-muted);`

---

## 9. Settings Overlay (triggered by START)

**Backdrop:**
```css
.overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,0.78);
  backdrop-filter: blur(14px);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none;
  transition: opacity 0.22s;
}
.overlay.open { opacity: 1; pointer-events: all; }
```

**Panel:**
```css
.settings-panel {
  width: 420px; max-height: 380px;
  background: var(--bg-overlay);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 18px; overflow: hidden;
  box-shadow: 0 28px 70px rgba(0,0,0,0.85);
  display: flex; flex-direction: column;
  transform: scale(0.92) translateY(10px);
  transition: transform 0.24s cubic-bezier(0.34, 1.4, 0.64, 1);
}
.overlay.open .settings-panel { transform: scale(1) translateY(0); }
```

**Panel layout:**
```
settings-panel
├── settings-header (flex-shrink:0, padding: 16px 20px 0)
│   ├── title row → "⚙ Settings" (16px 800) + ✕ close button (28×28, radius 8px)
│   └── tab row   → 3 equal tabs
└── settings-body (flex:1, overflow-y:auto, padding: 14px 20px 16px)
    └── tab content (swap via display:none / block)
```

**Tabs:**
```css
.stab {
  flex: 1; padding: 7px 0; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  font-size: 11.5px; font-weight: 600; color: var(--text-muted);
  background: rgba(255,255,255,0.04);
  border: 1.5px solid transparent;
  transition: all 0.15s;
}
.stab.active {
  background: var(--accent-dim);
  border-color: var(--accent);
  color: var(--accent);
}
```
Tab order: **WiFi** · **Bluetooth** · **Volume**

**Section label (used in all tabs):**
```css
font-size: 9.5px; font-weight: 700; letter-spacing: 0.12em;
color: var(--text-muted); text-transform: uppercase;
margin-bottom: 8px;
```

**Scrollbar in settings body:**
```css
.settings-body::-webkit-scrollbar { width: 4px; }
.settings-body::-webkit-scrollbar-track { background: transparent; }
.settings-body::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.10); border-radius: 2px; }
```

---

### 9a. WiFi Tab

**List item:**
```css
.wifi-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 12px; border-radius: 9px;
  border: 1.5px solid transparent; margin-bottom: 5px;
  background: rgba(255,255,255,0.04); transition: all 0.14s;
}
/* Currently connected network */
.wifi-item.sel {
  background: var(--accent-dim); border-color: var(--accent);
}
/* D-pad highlighted row */
.wifi-item.focused-item {
  border-color: rgba(255,255,255,0.20);
  background: rgba(255,255,255,0.07);
}
.wifi-item.focused-item.sel { border-color: var(--accent); }
```

Row contents: **signal bars widget** + **SSID name** (`flex:1; font-size: 12.5px; font-weight: 600`) + optional 🔒 + "● Connected" label in `var(--accent)`.

**Signal bar strength:**
- `.s4` — all 4 bars `var(--accent)` green
- `.s3` — bars 1–3 green, bar 4 `var(--text-dim)`
- `.s2` — bars 1–2 `var(--star)` amber, bars 3–4 `var(--text-dim)`

**Action buttons row:**
```css
.sett-btn {
  flex: 1; padding: 8px; border-radius: 8px;
  font-size: 12px; font-weight: 600; text-align: center;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08); color: var(--text);
}
.sett-btn.primary {
  background: rgba(34,197,94,0.15);
  border-color: rgba(34,197,94,0.35); color: var(--accent);
}
```
Buttons: "Refresh" (default) · "Connect" (primary)

---

### 9b. Bluetooth Tab

Same `.wifi-item` base pattern. Row: **device SVG icon** (16×16) + **name bold** + **type** (10px muted) + **status** right-aligned.

- Connected: icon stroke `var(--accent)`, status "● Connected" green
- Paired not connected: status "Paired" muted
- Newly discovered: status "Found", row opacity 0.6

**Scanning pulse dot:**
```css
.bt-scan-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--blue);
  animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1);   }
  50%       { opacity: 0.5; transform: scale(0.8); }
}
```
Placed beside "Looking for nearby devices" text.

Buttons: "Stop Scan" (default) · "Pair Device" (primary)

---

### 9c. Volume Tab

**Large display (centered):**
- Speaker SVG 28×28px
- Volume number: `font-family: 'Share Tech Mono'; font-size: 42px; font-weight: 800; color: white; min-width: 70px; text-align: center;`
- Label: "System Volume" `font-size: 11px; color: var(--text-muted);`

**Progress bar:**
```css
.vol-track {
  height: 8px; border-radius: 4px;
  background: rgba(255,255,255,0.10); overflow: hidden;
}
.vol-fill {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, #22c55e, #86efac);
  transition: width 0.15s;
}
```
Scale labels (0 / 25 / 50 / 75 / 100): `font-size: 9px; color: var(--text-dim);`

**± Buttons:**
```css
.vol-btn {
  flex: 1; height: 40px; border-radius: 10px;
  font-size: 22px; font-weight: 700; color: white;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.10);
  display: flex; align-items: center; justify-content: center;
}
.vol-btn.pressed { background: rgba(255,255,255,0.14); transform: scale(0.96); }
```

---

## 10. Game Launch Modal

Triggered when user confirms a focused card.

**Backdrop:** same `.overlay` structure, `z-index: 200`.

**Panel:**
```css
.launch-panel {
  width: 480px;
  background: var(--bg-overlay);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 18px; overflow: hidden;
  box-shadow: 0 28px 70px rgba(0,0,0,0.90);
  transform: scale(0.92);
  transition: transform 0.24s cubic-bezier(0.34, 1.4, 0.64, 1);
}
.launch-overlay.open .launch-panel { transform: scale(1); }
```

**Structure:**
```
launch-panel
├── thumbnail  (width: 100%, height: 160px, object-fit: cover)
└── launch-info (padding: 16px 20px 18px)
    ├── game name   — font-size: 18px, font-weight: 800
    ├── meta row    — flex tags: "by {dev}" · engine · price
    │                 tag style: padding 2px 8px, radius 4px,
    │                 background rgba(255,255,255,0.07), font-size 11px
    └── action row  — [Play Now] + [Cancel]
```

**Play Now:** `background: var(--accent); color: #000; font-weight: 700;` + play ▶ SVG icon (16×16) inline
**Cancel:** `background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.10); color: var(--text);`

Both: `flex: 1; height: 40px; border-radius: 10px; font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px;`

**Focus toggle (Play ↔ Cancel via Left/Right):**
- Focused button: `transform: scale(1.03); opacity: 1;`
- Unfocused button: `opacity: 0.6; transform: scale(1);`

---

## 11. Virtual Cursor

OS cursor is hidden (`cursor: none`). Render a DOM element as the visible cursor.

```css
#cursor {
  position: fixed; z-index: 500; pointer-events: none;
  width: 18px; height: 18px;
}
#cursor::before {
  content: '';
  position: absolute; top: 0; left: 0;
  width: 0; height: 0;
  border-left: 8px solid transparent;
  border-right: 4px solid transparent;
  border-top: 14px solid white;
  filter: drop-shadow(0 1px 3px rgba(0,0,0,0.8));
  transform-origin: top left;
}
/* A button held — cursor turns green */
#cursor.clicking::before { border-top-color: var(--accent); }
```

Secondary dot trailing the tip:
```css
#cursor-dot {
  position: fixed; z-index: 499; pointer-events: none;
  width: 6px; height: 6px; border-radius: 50%;
  background: rgba(255,255,255,0.35);
  /* positioned 13px below and 3px right of cursor origin */
}
```

**Analog stick → cursor movement:**
- Axes [0] (horizontal) and [1] (vertical) from `navigator.getGamepads()[0]`
- Deadzone: `0.15` — ignore input below this
- Speed: scales with stick deflection magnitude (`axis * speed * Math.abs(axis) * 2`)
- Clamp position to `[0, 800]` × `[0, 480]`

---

## 12. Toast Notification

```css
.toast {
  position: fixed; bottom: 48px; left: 50%;
  transform: translateX(-50%) translateY(14px);
  background: #1e1e24;
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 12px; padding: 10px 16px;
  display: flex; align-items: center; gap: 10px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.6);
  opacity: 0; pointer-events: none; white-space: nowrap;
  z-index: 300;
  transition: opacity 0.22s ease,
              transform 0.22s cubic-bezier(0.34, 1.4, 0.64, 1);
}
.toast.show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
```

Contents: emoji icon (font-size 16px) + vertical stack of title (12.5px bold) + subtitle (10.5px muted).
Auto-dismiss: 3.2 seconds.

**Trigger events:**
| Trigger | Icon | Title | Subtitle |
|---|---|---|---|
| Boot / gamepad connect | ✅ | "Controller Connected" | "Player 1 · Xbox Controller" |
| Launch game | ▶ | "Launching {game name}" | "Opening game…" |
| WiFi switch | 📶 | "WiFi Connected" | "{SSID name}" |
| Battery ≤ 15% | 🔋 | "Low Battery" | "{N}% remaining" |

---

## 13. Gamepad Input Mapping

```
Left analog stick  [axes 0,1]  →  Move virtual cursor (continuous, analog speed)
D-pad left         [button 14] →  Navigate card grid left
D-pad right        [button 15] →  Navigate card grid right
D-pad up           [button 12] →  Navigate card grid up
D-pad down         [button 13] →  Navigate card grid down
A button           [button 0]  →  Confirm / Click / Launch card
B button           [button 1]  →  Back / Close modal or settings
START              [button 9]  →  Open/close settings overlay
```

**Card grid navigation rules (3 columns × N rows):**
- No wrapping: blocked at grid edges
- Only one card holds `.focused` class at any time
- Remove `.focused` from previous, add to new index

**Inside Settings overlay:**
- Left/Right → cycle between WiFi / Bluetooth / Volume tabs
- Up/Down → move `.focused-item` highlight up/down the list
- Up/Down on Volume tab → adjust volume by ±5
- A → confirm action (WiFi: connect, BT: pair)
- B or START → close settings

**Inside Launch modal:**
- Left/Right → toggle focus between Play Now and Cancel
- A → execute focused button action
- B → close modal, return to grid

---

## 14. Implementation Checklist for Codex

- [ ] Do **not** modify any backend, API, or game-loading logic
- [ ] Apply all CSS as a single cohesive stylesheet — no separate files unless the project already uses them
- [ ] The `.focused` class on `.game-card` is JS-managed — only one card active at a time
- [ ] Settings overlay tabs are toggled via `display: none` / `display: block` — no routing
- [ ] `backdrop-filter: blur(14px)` is safe — Chromium kiosk guarantees support
- [ ] `#cursor` and `#cursor-dot` must be the last elements before `</body>`
- [ ] `overflow: hidden` on `html, body` — no native scrollbars anywhere on the main page
- [ ] All transitions assume stable 60fps on Pi 5 — do not reduce timing values
- [ ] Battery percentage should be read from the system if available, otherwise simulated
