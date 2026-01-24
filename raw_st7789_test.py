#!/usr/bin/env python3
"""raw_st7789_test.py

Low-level ST7789 SPI test (bypasses the `st7789` Python driver).

Use this when the display backlight turns on but you never see pixels.
It talks to /dev/spidev* via `spidev` and toggles DC/RST via GPIO.

Typical wiring (Raspberry Pi):
- MOSI: physical pin 19 (GPIO10)
- SCLK: physical pin 23 (GPIO11)
- CS:   physical pin 24 (CE0) or 26 (CE1)
- DC:   configurable (often physical pin 22 = GPIO25)
- RST:  configurable (often physical pin 18 = GPIO24)
- BLK:  either GPIO-controlled or tied to 3.3V
"""

from __future__ import annotations

import argparse
import time

import spidev

try:
    import RPi.GPIO as GPIO
except Exception as e:  # pragma: no cover
    raise SystemExit(f"RPi.GPIO not available: {e}")


_PHYS_TO_BCM = {
    3: 2,
    5: 3,
    7: 4,
    8: 14,
    10: 15,
    11: 17,
    12: 18,
    13: 27,
    15: 22,
    16: 23,
    18: 24,
    19: 10,
    21: 9,
    22: 25,
    23: 11,
    24: 8,
    26: 7,
    27: 0,
    28: 1,
    29: 5,
    31: 6,
    32: 12,
    33: 13,
    35: 19,
    36: 16,
    37: 26,
    38: 20,
    40: 21,
}


def _phys_to_bcm(phys_pin: int) -> int:
    bcm = _PHYS_TO_BCM.get(phys_pin)
    if bcm is None:
        raise ValueError(
            f"Physical pin {phys_pin} is not a GPIO pin. "
            "Use a GPIO-capable physical pin like 12, 18, 22, 23, 24, 26, etc."
        )
    return bcm


def _u16be(value: int) -> list[int]:
    return [(value >> 8) & 0xFF, value & 0xFF]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Raw ST7789 SPI test")
    p.add_argument("--port", type=int, default=0)
    p.add_argument("--cs", type=int, default=0, choices=[0, 1])
    p.add_argument("--speed", type=int, default=4_000_000)
    p.add_argument("--spi-mode", type=int, default=0, choices=[0, 1, 2, 3])

    p.add_argument("--width", type=int, default=240)
    p.add_argument("--height", type=int, default=240)
    p.add_argument("--offset-left", type=int, default=0)
    p.add_argument("--offset-top", type=int, default=0)

    p.add_argument("--rotation", type=int, default=90, choices=[0, 90, 180, 270])

    inv = p.add_mutually_exclusive_group()
    inv.add_argument("--invert", dest="invert", action="store_true")
    inv.add_argument("--no-invert", dest="invert", action="store_false")
    p.set_defaults(invert=True)

    p.add_argument("--dc", type=int, default=25, help="BCM GPIO for DC")
    p.add_argument("--rst", type=int, default=24, help="BCM GPIO for RST")
    p.add_argument("--no-rst", action="store_true", help="RST not connected")

    p.add_argument("--dc-phys", type=int, default=None, help="physical pin number for DC")
    p.add_argument("--rst-phys", type=int, default=None, help="physical pin number for RST")

    p.add_argument(
        "--fill",
        type=str,
        default="red",
        choices=["red", "green", "blue", "white", "black"],
        help="fill color",
    )
    return p


def _madctl(rotation: int, bgr: bool = True) -> int:
    # MADCTL bits: MY=0x80 MX=0x40 MV=0x20 ML=0x10 RGB/BGR=0x08 MH=0x04
    # This is a common mapping for ST7789; some boards vary.
    if rotation == 0:
        v = 0x00
    elif rotation == 90:
        v = 0x60
    elif rotation == 180:
        v = 0xC0
    elif rotation == 270:
        v = 0xA0
    else:
        v = 0x00
    if bgr:
        v |= 0x08
    return v


def main() -> int:
    args = _build_parser().parse_args()

    dc = _phys_to_bcm(args.dc_phys) if args.dc_phys is not None else args.dc
    rst = _phys_to_bcm(args.rst_phys) if args.rst_phys is not None else args.rst

    print(
        "Using (BCM): "
        f"port={args.port} cs={args.cs} speed={args.speed} mode={args.spi_mode} "
        f"dc={dc} rst={'none' if args.no_rst else rst} size={args.width}x{args.height} "
        f"offset=({args.offset_left},{args.offset_top}) rotation={args.rotation} invert={args.invert}"
    )

    spi = spidev.SpiDev()
    spi.open(args.port, args.cs)
    spi.max_speed_hz = args.speed
    spi.mode = args.spi_mode
    # ST7789 expects MSB-first.

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(dc, GPIO.OUT)
    if not args.no_rst:
        GPIO.setup(rst, GPIO.OUT)

    def cmd(c: int):
        GPIO.output(dc, GPIO.LOW)
        spi.writebytes([c & 0xFF])

    def data(bs: list[int] | bytes):
        GPIO.output(dc, GPIO.HIGH)
        spi.writebytes(list(bs))

    try:
        if not args.no_rst:
            GPIO.output(rst, GPIO.HIGH)
            time.sleep(0.05)
            GPIO.output(rst, GPIO.LOW)
            time.sleep(0.05)
            GPIO.output(rst, GPIO.HIGH)
            time.sleep(0.15)

        # Basic init sequence
        cmd(0x01)  # SWRESET
        time.sleep(0.15)

        cmd(0x11)  # SLPOUT
        time.sleep(0.12)

        cmd(0x3A)  # COLMOD
        data([0x55])  # 16-bit/pixel

        cmd(0x36)  # MADCTL
        data([_madctl(args.rotation, bgr=True)])

        if args.invert:
            cmd(0x21)  # INVON
        else:
            cmd(0x20)  # INVOFF

        cmd(0x13)  # NORON
        time.sleep(0.01)

        cmd(0x29)  # DISPON
        time.sleep(0.05)

        # Set address window
        x0 = args.offset_left
        y0 = args.offset_top
        x1 = args.offset_left + args.width - 1
        y1 = args.offset_top + args.height - 1

        cmd(0x2A)  # CASET
        data(_u16be(x0) + _u16be(x1))

        cmd(0x2B)  # RASET
        data(_u16be(y0) + _u16be(y1))

        cmd(0x2C)  # RAMWR

        color = {
            "red": (0xF8, 0x00),
            "green": (0x07, 0xE0),
            "blue": (0x00, 0x1F),
            "white": (0xFF, 0xFF),
            "black": (0x00, 0x00),
        }[args.fill]

        # Push a full-frame fill; chunk to avoid huge allocations.
        pixels = args.width * args.height
        chunk_pixels = 2048
        chunk = bytes([color[0], color[1]]) * chunk_pixels

        GPIO.output(dc, GPIO.HIGH)
        remaining = pixels
        while remaining > 0:
            n = chunk_pixels if remaining >= chunk_pixels else remaining
            spi.writebytes(chunk[: n * 2])
            remaining -= n

        print("Sent fill frame. If screen is still blank, it’s likely DC/RST wiring or panel/controller mismatch.")
        time.sleep(5)

        # Clear to black
        args.fill = "black"

        return 0
    finally:
        try:
            spi.close()
        finally:
            GPIO.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
