"""Hardware abstraction for the RVM.

Every physical action the kiosk needs goes through here. In this
prototype the implementations are SIMULATED (no real scanner, camera,
or slot motor). When the real Radxa-attached hardware is wired up, only
the bodies below change.

Public API:
    read_barcode()   -> str | None   (a scanned EAN/UPC, or None)
    open_slot()      -> None         (open the deposit door)
    capture_image()  -> str          (path/ref to the captured photo)
"""


# Barcodes that exist in data/bottles.json — used so the simulated
# "scan" returns something the rest of the flow can resolve.

from evdev import InputDevice, ecodes

# Your scanner device
scanner = InputDevice("/dev/input/event0")

KEYMAP = {
    "KEY_0": "0",
    "KEY_1": "1",
    "KEY_2": "2",
    "KEY_3": "3",
    "KEY_4": "4",
    "KEY_5": "5",
    "KEY_6": "6",
    "KEY_7": "7",
    "KEY_8": "8",
    "KEY_9": "9",
}


def read_barcode():
    print("Waiting for barcode scan...")

    barcode = ""

    for event in scanner.read_loop():

        if event.type != ecodes.EV_KEY:
            continue

        if event.value != 1:  # key pressed
            continue

        key = ecodes.KEY[event.code]

        if key == "KEY_ENTER":
            print("Scanned:", barcode)
            return barcode

        if key in KEYMAP:
            barcode += KEYMAP[key]


def open_slot():
    print("Opening slot...")
    return None


def capture_image():
    return "placeholder"
