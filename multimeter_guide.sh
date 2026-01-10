#!/bin/bash
cat << 'EOF'

================================================================================
                  HOW TO TEST SPI PINS WITH MULTIMETER
================================================================================

TOOLS NEEDED:
-------------
✓ Digital Multimeter (DMM)
✓ Raspberry Pi 3 with ST7789 connected
✓ Two multimeter probes (red and black)


STEP-BY-STEP PROCEDURE:
========================

STEP 1: Set Up Multimeter
--------------------------
1. Turn on your multimeter
2. Set dial to DC Voltage (DCV or V with straight line)
3. Set range to 20V (or auto-range if available)
4. Insert probes:
   - BLACK probe → COM port
   - RED probe → VΩmA port


STEP 2: Find Ground Reference
------------------------------
1. Connect BLACK probe to Raspberry Pi ground pin
   Recommended: Pin 6 (3rd pin down on right side)
   Other options: Pin 9, 14, 20, 25, 30, 34, or 39

2. Keep BLACK probe connected to ground throughout testing


STEP 3: Run Test Script
------------------------
On Raspberry Pi, run:
    python3 test_spi_multimeter.py

The script will continuously send data to the display.
Keep it running while you measure pins.


STEP 4: Measure Each Pin
-------------------------
Touch RED probe to each pin and note the voltage:

Pin Physical   GPIO    Signal   What You Should See
────────────────────────────────────────────────────────────────
    23         11      SCL      Voltage fluctuating (jumping)
                                between 0V and 3.3V rapidly
                                (Multimeter may show ~1.5V average)

    19         10      SDA      Voltage fluctuating (jumping)
                                between 0V and 3.3V rapidly
                                (Multimeter may show ~1.5V average)

    24          8      CS       Toggles between 0V and 3.3V
                                (May be steady at one value)

    22         25      DC       Toggles between 0V and 3.3V

    18         24      RST      Steady at ~3.3V (high)

    12         18      BL       Steady at ~3.3V (high)


WHAT FLUCTUATING MEANS:
-----------------------
• Multimeter reading jumps/changes rapidly
• May show values like 1.2V, 1.8V, 2.1V changing
• Indicates active data transmission
• This is GOOD - means signal is working


DIAGNOSIS:
==========

SCENARIO A: Both SCL (Pin 23) and SDA (Pin 19) fluctuating
-----------------------------------------------------------
✓ SPI is working correctly from Raspberry Pi side
→ If display still blank, problem is:
  • Display might be defective
  • Wrong display type/driver
  • Display wiring (at display end)


SCENARIO B: SCL (Pin 23) stuck at 0V or 3.3V (not fluctuating)
---------------------------------------------------------------
✗ SPI clock not working
→ Possible causes:
  • Wire not connected from Pin 23 to display SCL
  • Bad jumper wire
  • SPI not enabled (unlikely if script runs)
  • Pin 23 damaged (rare)


SCENARIO C: SDA (Pin 19) stuck at 0V or 3.3V (not fluctuating)
---------------------------------------------------------------
✗ SPI data not working
→ Possible causes:
  • Wire not connected from Pin 19 to display SDA
  • Bad jumper wire
  • Wrong pin connected


SCENARIO D: Both stuck, but CS/DC/RST/BL working
-------------------------------------------------
✗ SPI interface problem
→ Check:
  • Is SPI enabled? (run: ls /dev/spi*)
  • Is another program using SPI?
  • Reboot Pi and try again


ALTERNATIVE TEST (if fluctuation is hard to see):
==================================================

Your multimeter may be too slow to show rapid changes.

Try this instead:
1. Set multimeter to CONTINUITY mode (buzzer symbol)
2. Touch RED probe to Pin 23 or Pin 19
3. While script is running:
   - Should beep intermittently (on/off)
   - Or show continuity indicator blinking
4. This confirms signal is changing


ADVANCED: OSCILLOSCOPE VIEW
============================

If you have an oscilloscope:
- SCL should show a clean clock signal (square wave)
- SDA should show data patterns
- Frequency should match SPI speed (10 MHz in test script)


================================================================================

PHYSICAL PIN LOCATIONS (looking at Pi from above, USB ports on left):

        3.3V  [1 ] [2 ] 5V
              [3 ] [4 ] 5V
              [5 ] [6 ] GND ← BLACK probe here
              [7 ] [8 ]
        GND   [9 ] [10]
              [11] [12] GPIO 18 (BL)
              [13] [14]
              [15] [16]
        3.3V  [17] [18] GPIO 24 (RST)
    ┌→ GPIO 10 [19] [20] GND
    │         [21] [22] GPIO 25 (DC)
    └→ GPIO 11 [23] [24] GPIO 8 (CS)
              [25] [26]

    Pin 19 (SDA) and Pin 23 (SCL) are the critical ones to test!


================================================================================

SAFETY NOTES:
=============
✓ Multimeter set to DC Voltage (not AC or Amps)
✓ Don't short pins together with probe tips
✓ Be careful not to touch multiple pins at once
✓ 3.3V is safe - won't damage multimeter
✓ If you accidentally touch wrong pins, nothing will break


================================================================================

EOF
