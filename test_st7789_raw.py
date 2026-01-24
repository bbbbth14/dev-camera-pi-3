#!/usr/bin/env python3
"""test_st7789_raw.py

Raw ST7789 test suite (spidev + GPIO), based on the working init sequence in
raw_st7789_test.py.

Use this when the high-level `st7789` library shows backlight only.

Examples (your working wiring):
- Quick: python3 test_st7789_raw.py --quick --dc-phys 22 --rst-phys 18 --cs 0
- Full:  python3 test_st7789_raw.py --full  --dc-phys 22 --rst-phys 18 --cs 0

Notes:
- Pin flags ending with `-phys` are Raspberry Pi *physical* header pins.
- The driver expects BCM GPIO internally.
"""

from __future__ import annotations

import argparse
import time

import spidev
from PIL import Image, ImageDraw, ImageFont

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


def _madctl(rotation: int, bgr: bool = True) -> int:
    # MADCTL bits: MY=0x80 MX=0x40 MV=0x20 RGB/BGR=0x08
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


def _rgb888_to_rgb565_bytes(img: Image.Image) -> bytes:
    """Convert an RGB PIL image to RGB565 big-endian byte stream."""
    rgb = img.convert("RGB")
    data = rgb.tobytes()  # RGBRGB...
    out = bytearray(len(data) // 3 * 2)

    j = 0
    for i in range(0, len(data), 3):
        r = data[i]
        g = data[i + 1]
        b = data[i + 2]
        value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        out[j] = (value >> 8) & 0xFF
        out[j + 1] = value & 0xFF
        j += 2

    return bytes(out)


class RawST7789:
    def __init__(
        self,
        *,
        port: int,
        cs: int,
        dc: int,
        rst: int | None,
        speed: int,
        spi_mode: int,
        width: int,
        height: int,
        offset_left: int,
        offset_top: int,
        rotation: int,
        invert: bool,
    ):
        self.width = width
        self.height = height
        self.offset_left = offset_left
        self.offset_top = offset_top

        self._dc = dc
        self._rst = rst
        self._rotation = rotation
        self._invert = invert

        self._spi = spidev.SpiDev()
        self._spi.open(port, cs)
        self._spi.max_speed_hz = speed
        self._spi.mode = spi_mode

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._dc, GPIO.OUT)
        if self._rst is not None:
            GPIO.setup(self._rst, GPIO.OUT)

        self._init()

    def close(self) -> None:
        try:
            self._spi.close()
        finally:
            GPIO.cleanup()

    def _cmd(self, c: int) -> None:
        GPIO.output(self._dc, GPIO.LOW)
        self._spi.writebytes([c & 0xFF])

    def _data(self, bs: list[int] | bytes) -> None:
        GPIO.output(self._dc, GPIO.HIGH)
        self._spi.writebytes(list(bs))

    def _init(self) -> None:
        if self._rst is not None:
            GPIO.output(self._rst, GPIO.HIGH)
            time.sleep(0.05)
            GPIO.output(self._rst, GPIO.LOW)
            time.sleep(0.05)
            GPIO.output(self._rst, GPIO.HIGH)
            time.sleep(0.15)

        self._cmd(0x01)  # SWRESET
        time.sleep(0.15)

        self._cmd(0x11)  # SLPOUT
        time.sleep(0.12)

        self._cmd(0x3A)  # COLMOD
        self._data([0x55])  # 16-bit

        self._cmd(0x36)  # MADCTL
        self._data([_madctl(self._rotation, bgr=True)])

        self._cmd(0x21 if self._invert else 0x20)  # INVON/INVOFF

        self._cmd(0x13)  # NORON
        time.sleep(0.01)

        self._cmd(0x29)  # DISPON
        time.sleep(0.05)

    def set_window(self, x: int, y: int, w: int, h: int) -> None:
        x0 = self.offset_left + x
        y0 = self.offset_top + y
        x1 = x0 + w - 1
        y1 = y0 + h - 1

        self._cmd(0x2A)  # CASET
        self._data(_u16be(x0) + _u16be(x1))

        self._cmd(0x2B)  # RASET
        self._data(_u16be(y0) + _u16be(y1))

        self._cmd(0x2C)  # RAMWR

    def fill_rgb565(self, color_hi: int, color_lo: int) -> None:
        self.set_window(0, 0, self.width, self.height)
        pixels = self.width * self.height
        chunk_pixels = 2048
        chunk = bytes([color_hi, color_lo]) * chunk_pixels

        GPIO.output(self._dc, GPIO.HIGH)
        remaining = pixels
        while remaining > 0:
            n = chunk_pixels if remaining >= chunk_pixels else remaining
            self._spi.writebytes(chunk[: n * 2])
            remaining -= n

    def display_image(self, img: Image.Image) -> None:
        img = img.resize((self.width, self.height))
        self.set_window(0, 0, self.width, self.height)
        payload = _rgb888_to_rgb565_bytes(img)
        GPIO.output(self._dc, GPIO.HIGH)
        # chunk writes to avoid spidev overhead issues
        chunk = 4096
        for i in range(0, len(payload), chunk):
            self._spi.writebytes(payload[i : i + chunk])


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Raw ST7789 test suite")

    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true")
    mode.add_argument("--full", action="store_true")

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

    p.add_argument("--dc", type=int, default=25, help="BCM GPIO")
    p.add_argument("--rst", type=int, default=24, help="BCM GPIO")
    p.add_argument("--no-rst", action="store_true")

    p.add_argument("--dc-phys", type=int, default=None)
    p.add_argument("--rst-phys", type=int, default=None)

    return p


def _fonts():
    try:
        title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        return title, small
    except Exception:
        f = ImageFont.load_default()
        return f, f


def run_quick(d: RawST7789) -> None:
    # Solid red, then a centered text card.
    d.fill_rgb565(0xF8, 0x00)
    time.sleep(1)

    img = Image.new("RGB", (d.width, d.height), (0, 0, 80))
    draw = ImageDraw.Draw(img)
    title, small = _fonts()
    draw.rectangle([10, 10, d.width - 10, d.height - 10], outline=(255, 255, 255), width=2)
    draw.text((14, 16), "ST7789 RAW", font=title, fill=(255, 255, 0))
    draw.text((14, 50), "DISPLAY OK", font=title, fill=(255, 255, 255))
    draw.text((14, 90), f"{d.width}x{d.height}", font=small, fill=(200, 200, 200))
    d.display_image(img)
    time.sleep(3)


def run_full(d: RawST7789) -> None:
    colors = [
        ("WHITE", (0xFF, 0xFF)),
        ("RED", (0xF8, 0x00)),
        ("GREEN", (0x07, 0xE0)),
        ("BLUE", (0x00, 0x1F)),
        ("BLACK", (0x00, 0x00)),
    ]

    for name, (hi, lo) in colors:
        print(f"Showing {name}")
        d.fill_rgb565(hi, lo)
        time.sleep(0.8)

    # Color bars
    img = Image.new("RGB", (d.width, d.height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    bar_w = max(1, d.width // 6)
    bar_colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (0, 255, 255),
        (255, 0, 255),
    ]
    for i, c in enumerate(bar_colors):
        x0 = i * bar_w
        x1 = d.width if i == len(bar_colors) - 1 else (i + 1) * bar_w - 1
        draw.rectangle([x0, 0, x1, d.height], fill=c)

    title, small = _fonts()
    draw.rectangle([0, 0, d.width, 30], fill=(0, 0, 0))
    draw.text((6, 6), "ST7789 RAW FULL", font=small, fill=(255, 255, 255))
    d.display_image(img)
    time.sleep(3)

    # Final text screen
    img = Image.new("RGB", (d.width, d.height), (10, 60, 10))
    draw = ImageDraw.Draw(img)
    draw.text((12, d.height // 2 - 18), "ALL TESTS", font=title, fill=(255, 255, 255))
    draw.text((12, d.height // 2 + 10), "PASSED", font=title, fill=(255, 255, 0))
    d.display_image(img)
    time.sleep(2)


def main() -> int:
    args = _build_parser().parse_args()

    dc = _phys_to_bcm(args.dc_phys) if args.dc_phys is not None else args.dc
    rst = None
    if not args.no_rst:
        rst = _phys_to_bcm(args.rst_phys) if args.rst_phys is not None else args.rst

    print(
        "Using (BCM): "
        f"port={args.port} cs={args.cs} speed={args.speed} mode={args.spi_mode} "
        f"dc={dc} rst={'none' if rst is None else rst} size={args.width}x{args.height} "
        f"offset=({args.offset_left},{args.offset_top}) rotation={args.rotation} invert={args.invert}"
    )

    d = RawST7789(
        port=args.port,
        cs=args.cs,
        dc=dc,
        rst=rst,
        speed=args.speed,
        spi_mode=args.spi_mode,
        width=args.width,
        height=args.height,
        offset_left=args.offset_left,
        offset_top=args.offset_top,
        rotation=args.rotation,
        invert=args.invert,
    )

    try:
        if args.quick or (not args.quick and not args.full):
            run_quick(d)
        else:
            run_full(d)
        return 0
    finally:
        d.close()


if __name__ == "__main__":
    raise SystemExit(main())
