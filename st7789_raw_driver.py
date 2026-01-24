"""st7789_raw_driver.py

Minimal raw ST7789 driver (spidev + RPi.GPIO) for this repo.

Why:
- Some ST7789 modules work with raw init but show backlight-only with the
  high-level `st7789` Python library.

API:
- `RawST7789.display(image)` accepts a PIL RGB image.
- `RawST7789.fill_rgb565(hi, lo)` fills the screen with a solid color.

Pin numbering:
- `dc` / `rst` are BCM GPIO numbers.
- Use `phys_to_bcm()` if you have Raspberry Pi physical pin numbers.
"""

from __future__ import annotations

import time

import spidev
from PIL import Image

try:
    import RPi.GPIO as GPIO
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"RPi.GPIO not available: {e}")


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


def phys_to_bcm(phys_pin: int) -> int:
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
    rgb = img.convert("RGB")
    data = rgb.tobytes()
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
        offset_left: int = 0,
        offset_top: int = 0,
        rotation: int = 90,
        invert: bool = True,
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

    def display(self, img: Image.Image) -> None:
        """Compatibility with the `st7789` library: `.display(pil_image)`"""
        img = img.resize((self.width, self.height))
        self.set_window(0, 0, self.width, self.height)
        payload = _rgb888_to_rgb565_bytes(img)

        GPIO.output(self._dc, GPIO.HIGH)
        chunk = 4096
        for i in range(0, len(payload), chunk):
            self._spi.writebytes(payload[i : i + chunk])
