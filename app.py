"""Zephor RVM Kiosk — Flask app.

Lightweight touch-kiosk server for the reverse vending machine, intended
to run on a Radxa Zero 3W behind a full-screen kiosk browser.

Architecture:
  - Pages are server-rendered (templates/), one per screen of the flow.
  - All data lookups go through services.data_access (mock JSON now,
    cloud AWS API later) and all physical actions through
    services.hardware (simulated now, real GPIO/camera later).

Step 1 ships: the idle/attract screen and the JSON action endpoints.
Remaining screens (register/confirm/slot/bottle/thankyou) follow in
later steps.
"""

from flask import Flask, render_template, request, jsonify

from services import data_access, hardware

app = Flask(__name__)


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------
@app.route("/")
def idle():
    """Attract screen shown until a student touches the display."""
    return render_template("idle.html")


@app.route("/register")
def register():
    """Registration-number entry with an on-screen keyboard."""
    return render_template("register.html")


@app.route("/confirm")
def confirm():
    """Confirm the resolved student and choose scan vs no-barcode."""
    return render_template("confirm.html")


@app.route("/slot")
def slot():
    """Slot-open + camera-capture sequence (simulated hardware)."""
    return render_template("slot.html")


@app.route("/bottle")
def bottle():
    """Decoded bottle details (barcode path). Expanded in Step 4."""
    return render_template("bottle.html")


@app.route("/thankyou")
def thankyou():
    """Closing screen. Expanded in Step 4."""
    return render_template("thankyou.html")


# ----------------------------------------------------------------------
# JSON action endpoints
# These isolate the data/hardware layers from the front end, so the
# eventual swap to the cloud API needs no template changes.
# ----------------------------------------------------------------------
@app.route("/api/lookup", methods=["POST"])
def api_lookup():
    """Resolve a registration number to a student name + class."""
    reg_no = (request.get_json(silent=True) or {}).get("reg_no", "")
    student = data_access.lookup_student(reg_no)
    if not student:
        return jsonify({"found": False})
    return jsonify({
        "found": True,
        "reg_no": reg_no.strip().upper(),
        "name": student["name"],
        "class": student["class"],
    })


@app.route("/api/scan", methods=["POST"])
def api_scan():
    """Simulate a barcode scan and resolve the bottle details."""
    barcode = hardware.read_barcode()
    bottle = data_access.lookup_bottle(barcode)
    return jsonify({
        "scanned": bottle is not None,
        "barcode": barcode,
        "bottle": bottle,
    })


@app.route("/api/deposit", methods=["POST"])
def api_deposit():
    """Record a (simulated) deposit: open slot + capture photo.

    Accepts {reg_no, barcode|null}. barcode is null for the
    'no barcode but it's plastic' path.
    """
    payload = request.get_json(silent=True) or {}
    hardware.open_slot()
    image_ref = hardware.capture_image()
    return jsonify({
        "ok": True,
        "reg_no": payload.get("reg_no"),
        "barcode": payload.get("barcode"),
        "image": image_ref,
    })


if __name__ == "__main__":
    # Bind to all interfaces so the kiosk browser (or a dev machine on the
    # LAN) can reach it. Port 8000 to match run.sh / README.
    app.run(host="127.0.0.2", port=8000, debug=True)
