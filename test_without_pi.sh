#!/bin/bash
cat << 'EOF'

================================================================================
                   TESTING ST7789 DISPLAY WITHOUT RASPBERRY PI
================================================================================

METHOD 1: Using Arduino
----------------------------------------
If you have an Arduino (Uno, Nano, Mega, ESP32, etc.):

1. Install Adafruit ST7735 and ST7789 library in Arduino IDE
2. Use this wiring:
   Arduino → ST7789
   -------------------------
   5V/3.3V → VCC
   GND     → GND
   Pin 13  → SCL (SCLK)
   Pin 11  → SDA (MOSI)
   Pin 10  → CS
   Pin 9   → DC
   Pin 8   → RST
   Pin 7   → BL (or 3.3V directly)

3. Load example sketch: File → Examples → Adafruit ST7789 → graphicstest
4. If display shows colorful graphics → Display is WORKING ✓


METHOD 2: Using ESP32/ESP8266
----------------------------------------
Similar to Arduino but uses different pins (check ESP32 pinout)
Uses same Adafruit ST7789 library


METHOD 3: Direct Power Test (SIMPLEST)
----------------------------------------
To verify display is not dead:

1. Connect ONLY these 3 wires:
   Display VCC → 3.3V power supply (or battery)
   Display GND → Ground
   Display BL  → 3.3V (or VCC)

2. What you should see:
   ✓ Backlight turns ON → Display has power, not dead
   • May show white, black, or random colors (this is normal without data)

This confirms the display panel itself is alive.


METHOD 4: Multimeter Test
----------------------------------------
To check if display is receiving signals:

1. Set multimeter to voltage mode (DC)
2. Connect display to Raspberry Pi normally
3. Run a test script on Pi
4. Measure with multimeter:
   - Between SCL pin and GND → Should see voltage fluctuating (0-3.3V)
   - Between SDA pin and GND → Should see voltage fluctuating (0-3.3V)
   
If voltages are stuck at 0V or 3.3V (not changing):
→ No data is reaching those pins


METHOD 5: Swap with Known-Working Display
----------------------------------------
If you have another ST7789 display or a friend has one:
- Try your display on their working setup
- Try their display on your Pi

This quickly identifies if problem is display or Pi wiring.


METHOD 6: Visual Inspection
----------------------------------------
Check the display itself:

1. Look for physical damage:
   - Cracked screen
   - Damaged ribbon cable
   - Bent pins
   - Burn marks

2. Check solder joints on back:
   - Cold solder joints
   - Broken traces
   - Missing components


METHOD 7: Test with Different Wiring
----------------------------------------
Sometimes the issue is with jumper wires, not the display:

1. Use different jumper wires (especially for SCL/SDA)
2. Use shorter wires if possible
3. Ensure firm connections
4. Try male-to-female vs female-to-female wires


METHOD 8: Check Display Documentation
----------------------------------------
Your display may have specific requirements:

1. Check if it's 3.3V or 5V compatible
2. Some displays need pull-up resistors on SDA/SCL
3. Some need specific initialization sequences
4. Check if CS pin needs pull-down resistor


================================================================================
                           QUICK DIAGNOSIS GUIDE
================================================================================

Symptom: Backlight ON, no image
Likely cause: SCL or SDA not connected, or display needs different init

Symptom: Nothing at all (no backlight)
Likely cause: No power (VCC/GND not connected)

Symptom: Backlight flickers
Likely cause: Loose power connection or insufficient current

Symptom: Random colors/garbage
Likely cause: Wrong initialization or timing issues

Symptom: Dim display
Likely cause: Backlight not at full power


================================================================================
                         RECOMMENDED TESTS
================================================================================

Since you have backlight working:

1. FIRST: Try different jumper wires for SCL and SDA
   → This is the most common issue

2. SECOND: Try swapping SCL and SDA connections
   → Maybe they're labeled backwards on your display

3. THIRD: Reduce SPI speed in code:
   Change: spi_speed_hz=80 * 1000000
   To:     spi_speed_hz=10 * 1000000
   → Some displays can't handle high speeds

4. FOURTH: Try different rotation values (0, 90, 180, 270)
   → Display might be working but rotated wrong


================================================================================

EOF
