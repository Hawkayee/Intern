# Zephor RVM Kiosk

Lightweight touch-kiosk web app for the Zephor reverse vending machine (RVM).
Runs on a **Radxa Zero 3W** driving an **18.5" touch display (1366×768, landscape)**.

This is a **wireframe prototype**: hardware (barcode scanner, camera, slot) is
simulated, and student/bottle data comes from local mock JSON. Both are isolated
behind swappable service modules so the real cloud API and hardware can drop in
later without touching the front end.

## Stack
- Flask (single lightweight process), server-rendered Jinja2 templates
- Vanilla JS + CSS (no build step), fonts bundled locally for offline use

## Project layout
```
app.py                 Flask routes (pages + /api/* action endpoints)
data/
  students.json        mock: reg_no -> {name, class}
  bottles.json         mock: barcode -> {brand, size, type, points}
services/
  data_access.py       lookup_student / lookup_bottle   <-- swap to AWS API later
  hardware.py          read_barcode / open_slot / capture_image  <-- real hardware later
templates/             one template per screen
static/                css, js, bundled fonts, Zephor logo
```

## Run (development)
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run.sh
```
Then open <http://localhost:8000>. For a faithful preview, size the browser
window to **1366×768**.

## Run on the Radxa (kiosk mode)
Start the server on boot, then launch a full-screen browser pointed at it, e.g.:
```bash
chromium-browser --kiosk --incognito --noerrdialogs \
  --disable-pinch --overscroll-history-navigation=0 \
  http://localhost:8000
```
(Auto-start on boot / display rotation are out of scope for this prototype.)

## Status — prototype complete
- [x] **Step 1** — scaffold + light Zephor theme + idle/attract screen + `/api/*` endpoints
- [x] **Step 2** — registration entry (on-screen keyboard, `/api/lookup`)
- [x] **Step 3** — confirm student → slot/capture (scan vs no-barcode paths)
- [x] **Step 4** — bottle details + thank-you + idle auto-reset

## Flow
`idle → register → confirm → slot/capture → (bottle → )thankyou → idle`

Interactive screens auto-return to idle after 45s of no touch; the thank-you
screen auto-returns after a 10s countdown.

## Mock test data
- Registration numbers: `22ZS101` … `22ZS105` (e.g. `22ZS101` = Aarav Sharma, 8B)
- Barcodes: `8901234567890` … `8901234567893`
