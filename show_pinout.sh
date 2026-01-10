#!/bin/bash
# Visual Pin Guide for ST7789 on Raspberry Pi

cat << 'EOF'

================================================================================
                    RASPBERRY PI GPIO PINOUT FOR ST7789
================================================================================

    3.3V  [ 1] [2 ] 5V
           [ 3] [4 ] 5V              ┌─────────────────┐
           [ 5] [6 ] GND ────────────┤ GND             │
           [ 7] [8 ]                 │                 │
    GND    [ 9] [10]                 │   ST7789 LCD    │
           [11] [12] GPIO 18 ────────┤ BL (Backlight)  │
           [13] [14] GND             │                 │
           [15] [16]                 │                 │
    3.3V   [17] [18] GPIO 24 ────────┤ RST (Reset)     │
 GPIO 10   [19] [20] GND             │                 │
           [21] [22] GPIO 25 ────────┤ DC              │
 GPIO 11   [23] [24] GPIO 8  ────────┤ CS              │
    GND    [25] [26]                 │                 │
           [27] [28]                 └─────────────────┘
           [29] [30]
           [31] [32]
           [33] [34]
           [35] [36]
           [37] [38]
    GND    [39] [40]


================================================================================
                            CRITICAL CONNECTIONS
================================================================================

POWER (choose one VCC and one GND):
  VCC  ───→  3.3V     (Pin 1 or Pin 17)
  GND  ───→  Ground   (Pin 6, 9, 14, 20, 25, 30, 34, or 39)

HARDWARE SPI (ONLY ONE OPTION - CANNOT CHANGE):
  SCL  ───→  GPIO 11  (Pin 23)  ⚠️  THIS IS THE ONLY SPI CLOCK PIN
  SDA  ───→  GPIO 10  (Pin 19)  ⚠️  THIS IS THE ONLY SPI DATA PIN

CONTROL PINS (can use different GPIOs if needed):
  CS   ───→  GPIO 8   (Pin 24)  - Chip Select
  DC   ───→  GPIO 25  (Pin 22)  - Data/Command
  RST  ───→  GPIO 24  (Pin 18)  - Reset
  BL   ───→  GPIO 18  (Pin 12)  - Backlight


================================================================================
                               IMPORTANT NOTES
================================================================================

1. There is ONLY ONE hardware SPI interface on most Raspberry Pi models
   - SCL (clock) = GPIO 11 ONLY
   - SDA (data)  = GPIO 10 ONLY

2. These pins are HARDWIRED in the Raspberry Pi's hardware SPI controller
   - You CANNOT use other GPIO pins for SCL/SDA with hardware SPI
   - The st7789 Python library uses hardware SPI

3. If your display has labels:
   - SCL = SCLK = CLK = Clock
   - SDA = MOSI = DIN = Data Input
   (All refer to the same pins: GPIO 11 and GPIO 10)

4. Check your connections with a multimeter if possible:
   - Pin 23 (GPIO 11) → Display SCL/SCLK
   - Pin 19 (GPIO 10) → Display SDA/MOSI


================================================================================
                            QUICK VERIFICATION
================================================================================

Run this command to verify GPIO 10 and 11 are in SPI mode:

    gpio readall | grep -E "GPIO 10|GPIO 11"

Or use:

    pinout

To see your Raspberry Pi's pinout diagram.


================================================================================

EOF
