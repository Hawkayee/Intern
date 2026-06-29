#!/usr/bin/env python3
"""
Raspberry Pi controller for the ESP32-CAM serial capture firmware.

It opens the serial port, waits for the ESP to say "READY", then for each
capture it sends "CAPTURE", reads the framed base64 stream, decodes it,
verifies the length, and saves a timestamped .jpg.

Usage:
    python3 rpi_capture.py                      # auto-detect port, one shot
    python3 rpi_capture.py --interval 10        # one shot every 10 seconds
    python3 rpi_capture.py --count 5            # take 5 shots then stop
    python3 rpi_capture.py --port /dev/ttyUSB0  # force a port

Memory note: lines are streamed and joined once at the end; nothing about the
image is held in RAM longer than the single decode, so this is light enough for
the Pi to run indefinitely.
"""

import argparse
import base64
import glob
import os
import sys
import time
from datetime import datetime

try:
    import serial  # pyserial
except ImportError:
    sys.exit("pyserial is missing. Install it with: pip3 install pyserial")

BEGIN = "---BEGIN IMAGE---"
END = "---END IMAGE---"


def autodetect_port():
    # CH340 / CP210x show up as ttyUSB*, native USB-CDC ESP32 as ttyACM*.
    for pattern in ("/dev/ttyUSB*", "/dev/ttyACM*"):
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[0]
    return None


def open_serial(port, baud):
    # The ESP32-CAM-MB baseboard wires auto-reset to the DTR/RTS lines.
    # pyserial asserts DTR on open by default, which holds the chip in reset
    # and produces a meaningless byte flood instead of sketch output. We build
    # the port object first, force DTR/RTS low, THEN open. timeout=2 keeps the
    # readline() deadline loops from hanging.
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = baud
    ser.timeout = 2
    ser.dtr = False
    ser.rts = False
    ser.open()
    return ser


def wait_for_ready(ser, timeout=12):
    # Opening the port briefly toggles DTR/RTS on most CH340 boards, which can
    # nudge the ESP into a reboot. During boot (banner + camera init + warm-up)
    # it isn't reading serial yet, so a single early PING gets dropped. We give
    # it a moment to settle, then PING repeatedly until it answers PONG/READY.
    time.sleep(2.0)                 # let any boot-on-open finish
    deadline = time.time() + timeout
    while time.time() < deadline:
        ser.reset_input_buffer()    # drop the 115200 boot banner (garbage at our baud)
        ser.write(b"PING\n")
        ser.flush()
        end_probe = time.time() + 1.0
        while time.time() < end_probe:
            line = ser.readline().decode("ascii", "ignore").strip()
            if line in ("PONG", "READY"):
                return True
            if line.startswith("ERROR"):
                print("  ESP reports:", line)
    return False


def set_flash(ser, level):
    """Set the flash brightness (0-255) used by flash captures."""
    ser.reset_input_buffer()
    ser.write(f"FLASH:{level}\n".encode())
    ser.flush()
    end = time.time() + 1.0
    while time.time() < end:
        if ser.readline().strip() == b"OK":
            return True
    return False


def capture_one(ser, save_dir, use_flash=False, overall_timeout=60):
    ser.reset_input_buffer()
    ser.write(b"CAPTUREF\n" if use_flash else b"CAPTURE\n")
    ser.flush()

    deadline = time.time() + overall_timeout

    # 1) wait for the BEGIN marker
    while True:
        if time.time() > deadline:
            raise TimeoutError("no BEGIN marker (is the ESP running the right sketch?)")
        line = ser.readline().decode("ascii", "ignore").strip()
        if line == BEGIN:
            break
        if line.startswith("ERROR"):
            raise RuntimeError(f"ESP error: {line}")

    # 2) collect lines until END, picking out the LEN header
    expected = None
    chunks = []
    while True:
        if time.time() > deadline:
            raise TimeoutError("no END marker (transfer interrupted)")
        line = ser.readline().decode("ascii", "ignore").strip()
        if not line:
            continue
        if line.startswith("LEN:"):
            try:
                expected = int(line[4:])
            except ValueError:
                expected = None
            continue
        if line == END:
            break
        if line.startswith("ERROR"):
            raise RuntimeError(f"ESP error during transfer: {line}")
        chunks.append(line)

    b64 = "".join(chunks)
    data = base64.b64decode(b64)

    if expected is not None and len(data) != expected:
        print(f"  WARNING: length mismatch (got {len(data)}, expected {expected}) "
              f"-- image may be corrupted")

    os.makedirs(save_dir, exist_ok=True)
    name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
    path = os.path.join(save_dir, name)
    with open(path, "wb") as f:
        f.write(data)

    print(f"  Saved {path} ({len(data)} bytes)")
    return path


def main():
    ap = argparse.ArgumentParser(description="ESP32-CAM serial capture controller")
    ap.add_argument("--port", default=None, help="serial device (default: auto-detect)")
    ap.add_argument("--baud", type=int, default=921600, help="baud rate (must match the sketch)")
    ap.add_argument("--dir", default="captures", help="output directory")
    ap.add_argument("--interval", type=float, default=0.0,
                    help="seconds between shots; 0 = single shot")
    ap.add_argument("--count", type=int, default=0,
                    help="number of shots before exiting; 0 = unlimited (with --interval)")
    ap.add_argument("--flash", type=int, default=100, metavar="0-255",
                    help="flash LED brightness (default 100); set 0 to disable")
    args = ap.parse_args()

    port = args.port or autodetect_port()
    if not port:
        sys.exit("No serial port found. Plug in the ESP32 or pass --port /dev/ttyUSB0")

    print(f"Opening {port} @ {args.baud} ...")
    ser = open_serial(port, args.baud)

    print("Checking link to ESP (PING) ...")
    if wait_for_ready(ser):
        print("ESP responded; link OK.")
    else:
        print("No PONG/READY from ESP (continuing anyway).")

    use_flash = args.flash > 0
    if use_flash:
        level = max(0, min(255, args.flash))
        print(f"Setting flash brightness to {level} ...")
        set_flash(ser, level)

    try:
        shot = 0
        while True:
            shot += 1
            print(f"[{shot}] Requesting capture ...")
            try:
                capture_one(ser, args.dir, use_flash=use_flash)
            except Exception as e:
                print(f"  Capture failed: {e}")

            if args.count and shot >= args.count:
                break
            if args.interval <= 0:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
