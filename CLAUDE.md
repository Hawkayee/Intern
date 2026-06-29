# CLAUDE.md — Zephor RVM Kiosk

Guidance for Claude Code (and humans) working in this repository.

## What this is
A lightweight **touch-kiosk web app** that runs **on the Zephor reverse vending
machine (RVM)**. It guides a student through depositing a plastic bottle:

```
idle → register → confirm → slot/capture → (bottle →) thankyou → idle
```

Target hardware: a **Radxa Zero 3W** (ARM, limited RAM) driving an **18.5" touch
display at 1366×768, landscape**. It can also run on any desktop for testing.

Current state: a **wireframe prototype**. Hardware (barcode scanner, camera, slot
door) is **simulated**, and student/bottle data comes from **local mock JSON**.
This is intentional — see "Swap points" below.

## Non-negotiable constraints
- **Stay lightweight.** Server-rendered Jinja2 + vanilla JS/CSS. No frontend
  framework, no build step, no bundler. The Radxa is resource-limited.
- **Light theme only.** Never introduce dark mode. Surfaces are warm off-white.
- **Stick to the Zephor brand.** Accent orange `#f15a24`, fonts Playfair Display
  (headings) + Manrope (body), the phoenix logo. Fonts are bundled locally in
  `static/fonts/` (no CDN) so the kiosk works offline.
- **Touch-first.** No hover-only behaviour. Big targets (buttons ≥ ~68px tall).
  Touch hardening (no zoom/select) lives in `static/css/kiosk.css`.

## Architecture
- `app.py` — Flask app. One route per screen + three JSON action endpoints
  (`/api/lookup`, `/api/scan`, `/api/deposit`).
- `templates/` — one template per screen, all extending `base.html`.
- `static/css/kiosk.css` — the whole theme + every screen's styles (single file).
- `static/js/kiosk.js` — shared client helpers under the global `ZephorKiosk`:
  `buildKeyboard`, `startIdleTimeout`, `postJSON`, and `setState`/`getState`/
  `clearState` (flow state is carried between page screens via `sessionStorage`
  under the `zephor.*` namespace).

### Swap points (the important bit)
Everything that will become "real" later is isolated in two modules. Change only
their function bodies — **callers must not change**:

- `services/data_access.py` — `lookup_student(reg_no)`, `lookup_bottle(barcode)`.
  Reads `data/*.json` now → becomes HTTP calls to the **cloud (AWS) API** later.
- `services/hardware.py` — `read_barcode()`, `open_slot()`, `capture_image()`.
  Simulated now → becomes real GPIO / camera drivers later.

If you need new data or a new physical action, add a function to one of these
modules rather than inlining a file read / fetch / GPIO call in a route.

## The flow, screen by screen
1. **idle** (`/`) — attract screen; any touch → register (clears session).
2. **register** (`/register`) — on-screen keyboard → `POST /api/lookup`.
   Found → store `student`, go to confirm. Not found → inline error.
3. **confirm** (`/confirm`) — shows name/class; two paths:
   - *Simulate scan* → `POST /api/scan` → store `deposit` (with bottle) → slot.
   - *No barcode — it's plastic* → store `deposit` (barcode `null`) → slot.
4. **slot** (`/slot`) — door-open + capture animation, `POST /api/deposit`,
   then routes by `deposit.barcode`: present → bottle, null → thankyou.
5. **bottle** (`/bottle`) — decoded bottle details + points, OK → thankyou.
6. **thankyou** (`/thankyou`) — success state; auto-returns to idle (10s).

Interactive screens auto-return to idle after 45s of inactivity
(`ZephorKiosk.startIdleTimeout`).

## Conventions
- Each downstream screen guards against direct access: if its required
  `sessionStorage` state is missing, it redirects to `/`. Keep this when adding
  screens.
- Keep all styles in `kiosk.css` and all shared JS in `kiosk.js` — per-page
  `<script>` blocks should only wire that page, not define reusable helpers.
- Mock test data: reg numbers `22ZS101`–`22ZS105`; barcodes
  `8901234567890`–`8901234567893`. Keep `data/*.json` in sync if you add cases.

## Run & verify
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run.sh                      # serves http://0.0.0.0:8000
```
Smoke test without a browser:
```bash
curl -s -XPOST localhost:8000/api/lookup -H 'Content-Type: application/json' \
  -d '{"reg_no":"22ZS101"}'          # -> Aarav Sharma / 8B
curl -s -XPOST localhost:8000/api/scan          # -> a bottle + barcode
curl -s -XPOST localhost:8000/api/deposit -H 'Content-Type: application/json' \
  -d '{"reg_no":"22ZS101","barcode":null}'
```
Manual: open at 1366×768, walk both the scan and no-barcode paths.

## Do NOT
- Add dark mode, a JS framework, or a build step.
- Inline data access or hardware calls in routes/templates — use the service
  modules.
- Commit `.venv/` or `__pycache__/` (see `.gitignore`).
