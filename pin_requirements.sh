#!/bin/bash
cat << 'EOF'

================================================================================
                    ST7789 PINS - REQUIRED vs OPTIONAL
================================================================================

ABSOLUTELY REQUIRED (Minimum to work):
----------------------------------------
✓ VCC   → 3.3V (Pin 1 or 17)           - Power supply
✓ GND   → Ground (Pin 6, 9, 14, etc.)  - Ground
✓ SCL   → GPIO 11 (Pin 23)             - SPI Clock (data won't transfer without this)
✓ SDA   → GPIO 10 (Pin 19)             - SPI Data (data won't transfer without this)
✓ DC    → GPIO 25 (Pin 22)             - Data/Command control
✓ CS    → GPIO 8 (Pin 24)              - Chip Select

RECOMMENDED (Display won't work well without these):
----------------------------------------------------
✓ RST   → GPIO 24 (Pin 18)             - Reset (needed for proper initialization)
✓ BL    → GPIO 18 (Pin 12)             - Backlight (display will be dark without this)

OPTIONAL (May not exist on your display):
------------------------------------------
⚬ MISO  → (not needed for ST7789)      - Display doesn't send data back
⚬ 3.3V  → (might be labeled twice)     - Just connect VCC once
⚬ LED+  → (same as BL)                 - Some displays label backlight differently
⚬ LED-  → (might need GND)             - Some displays have separate backlight ground


================================================================================
                         MINIMAL WORKING SETUP
================================================================================

If you want to test with MINIMUM connections (6 wires + 2 power):

Required Wires:
1. VCC  → 3.3V (Pin 1)
2. GND  → Ground (Pin 6)
3. SCL  → GPIO 11 (Pin 23)  ⚠️
4. SDA  → GPIO 10 (Pin 19)  ⚠️
5. DC   → GPIO 25 (Pin 22)
6. CS   → GPIO 8 (Pin 24)
7. RST  → GPIO 24 (Pin 18)
8. BL   → GPIO 18 (Pin 12)

TOTAL: 8 wires


================================================================================
                      WHAT HAPPENS IF YOU SKIP PINS?
================================================================================

Missing VCC/GND:    Display is completely dead (no power)
Missing SCL:        Backlight may work, but NO IMAGE (no clock signal)
Missing SDA:        Backlight may work, but NO IMAGE (no data transfer)
Missing DC:         Random colors or garbage on screen
Missing CS:         Display won't respond
Missing RST:        Display might not initialize properly
Missing BL:         Display works but screen is DARK (backlight off)


================================================================================
                        YOUR CURRENT ISSUE
================================================================================

Symptom: Backlight ON, but NO IMAGE

This means:
  ✓ VCC, GND, BL are connected correctly (power and backlight work)
  ✗ SCL or SDA has a problem (data is not reaching the display)

Check:
  1. Is SCL connected to Pin 23 (GPIO 11)?
  2. Is SDA connected to Pin 19 (GPIO 10)?
  3. Are the wires firmly pushed in?
  4. Try swapping SCL and SDA (maybe they're reversed)
  5. Try different wires for SCL and SDA


================================================================================
                           SUMMARY
================================================================================

Minimum pins needed:  8 wires
  • 2 for power (VCC, GND)
  • 2 for SPI data (SCL, SDA) ← MOST IMPORTANT FOR IMAGE
  • 4 for control (DC, CS, RST, BL)

You do NOT need:
  • MISO pin
  • Multiple VCC or GND (just one of each)

EOF
