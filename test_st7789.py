#!/usr/bin/env python3
"""test_st7789.py

ST7789/ST7789V3 SPI display test.

This repo’s other tools (e.g. `display_attendance.py`, `check_st7789_wiring.py`)
use the following *default* wiring, so this test does too:

- SPI: port 0, CS0 (CE0 / GPIO 8)
- DC: GPIO 25
- RST: GPIO 24
- Backlight: GPIO 18
- Rotation: 90

If your module differs (some 240x240 panels need offsets, some use different
GPIOs), pass overrides via CLI flags.
"""

import argparse
import time

import st7789
from PIL import Image, ImageDraw, ImageFont


_PHYS_TO_BCM = {
    # Power pins (no BCM mapping): 1=3V3, 2=5V, 4=5V, 6/9/14/20/25/30/34/39=GND
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
            f"Physical pin {phys_pin} is not a GPIO pin (or is unsupported). "
            "Use a GPIO-capable physical pin like 12, 18, 22, 23, 24, etc."
        )
    return bcm

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ST7789/ST7789V3 display test")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true", help="run a quick sanity test")
    mode.add_argument("--full", action="store_true", help="run the full test suite (default)")
    mode.add_argument(
        "--scan",
        action="store_true",
        help="cycle common rotation/offset/invert settings until you see an image",
    )

    parser.add_argument("--rotation", type=int, default=90, choices=[0, 90, 180, 270])
    parser.add_argument("--port", type=int, default=0, help="SPI port (usually 0)")
    parser.add_argument("--cs", type=int, default=0, choices=[0, 1], help="SPI chip select (0=CE0, 1=CE1)")
    parser.add_argument("--dc", type=int, default=25, help="GPIO for DC/RS")
    parser.add_argument("--rst", type=int, default=24, help="GPIO for RST/RES")
    parser.add_argument("--backlight", type=int, default=18, help="GPIO for backlight (BL/BLK)")

    parser.add_argument(
        "--dc-phys",
        type=int,
        default=None,
        help="physical header pin for DC/RS (e.g. 22 for GPIO25)",
    )
    parser.add_argument(
        "--rst-phys",
        type=int,
        default=None,
        help="physical header pin for RST/RES (e.g. 18 for GPIO24)",
    )
    parser.add_argument(
        "--backlight-phys",
        type=int,
        default=None,
        help="physical header pin for BL/BLK (e.g. 12 for GPIO18)",
    )
    parser.add_argument(
        "--no-backlight",
        action="store_true",
        help="do not control backlight via GPIO (use when BLK is tied to 3.3V)",
    )
    parser.add_argument(
        "--no-rst",
        action="store_true",
        help="do not use a reset GPIO (use when RST is not connected)",
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=4_000_000,
        help="SPI speed in Hz (start low; raise once working)",
    )

    invert = parser.add_mutually_exclusive_group()
    invert.add_argument("--invert", dest="invert", action="store_true", help="enable color invert")
    invert.add_argument("--no-invert", dest="invert", action="store_false", help="disable color invert")
    parser.set_defaults(invert=True)

    parser.add_argument("--width", type=int, default=None, help="override panel width")
    parser.add_argument("--height", type=int, default=None, help="override panel height")
    parser.add_argument("--offset-left", type=int, default=None, help="optional left offset")
    parser.add_argument("--offset-top", type=int, default=None, help="optional top offset")

    return parser


def _init_display(args: argparse.Namespace):
    dc_gpio = _phys_to_bcm(args.dc_phys) if args.dc_phys is not None else args.dc
    rst_gpio = _phys_to_bcm(args.rst_phys) if args.rst_phys is not None else args.rst
    backlight_gpio = (
        _phys_to_bcm(args.backlight_phys) if args.backlight_phys is not None else args.backlight
    )

    kwargs = dict(
        rotation=args.rotation,
        port=args.port,
        cs=args.cs,
        dc=dc_gpio,
        invert=args.invert,
        spi_speed_hz=args.speed,
    )

    if not args.no_rst:
        kwargs["rst"] = rst_gpio

    if not args.no_backlight:
        kwargs["backlight"] = backlight_gpio

    if args.width is not None:
        kwargs["width"] = args.width
    if args.height is not None:
        kwargs["height"] = args.height
    if args.offset_left is not None:
        kwargs["offset_left"] = args.offset_left
    if args.offset_top is not None:
        kwargs["offset_top"] = args.offset_top

    return st7789.ST7789(**kwargs)


def scan_for_working_config(base_args: argparse.Namespace) -> None:
    """Cycle common configs. Stop when you see any image."""
    candidates_rotation = [0, 90, 180, 270]
    # 240x280 panels often need a top offset (commonly ~20), but varies by vendor.
    candidates_offset_top = [0, 20, 40, 60, 80, 100, 120]
    candidates_offset_left = [0]
    candidates_invert = [True, False]
    candidates_speed = [4_000_000, 8_000_000, 12_000_000, 16_000_000, 24_000_000, 32_000_000]
    candidates_size = [(240, 240), (240, 280), (240, 320)]
    candidates_cs = [0, 1]
    candidates_no_rst = [False, True]
    candidates_no_backlight = [base_args.no_backlight, True] if not base_args.no_backlight else [True]

    # Backlight-only but no pixels is very often caused by wrong DC/RST wiring.
    # Try a few common GPIO pin sets across ST7789/ST7789V3 modules.
    candidates_pin_sets = [
        (base_args.dc, base_args.rst, base_args.backlight),
        (25, 24, 18),  # common tutorials/hats
        (9, 25, 13),   # common small ST7789V3 modules
        (27, 22, 18),  # occasional alternative wiring
    ]

    print("\nSCAN MODE")
    print("- Watch the screen; when you see ANYTHING, note the printed config.")
    print("- If you never see anything, the issue is likely wiring/power/CS/DC/RST.")

    trial = 0
    for width, height in candidates_size:
        for dc, rst, backlight in candidates_pin_sets:
            for rotation in candidates_rotation:
                for offset_top in candidates_offset_top:
                    for offset_left in candidates_offset_left:
                        for invert in candidates_invert:
                            for speed in candidates_speed:
                                for cs in candidates_cs:
                                    for no_rst in candidates_no_rst:
                                        for no_backlight in candidates_no_backlight:
                                            trial += 1

                                            args = argparse.Namespace(**vars(base_args))
                                            args.width = width
                                            args.height = height
                                            args.dc = dc
                                            args.rst = rst
                                            args.backlight = backlight
                                            args.rotation = rotation
                                            args.offset_top = offset_top
                                            args.offset_left = offset_left
                                            args.invert = invert
                                            args.speed = speed
                                            args.cs = cs
                                            args.no_rst = no_rst
                                            args.no_backlight = no_backlight

                                            print(
                                                f"\n[Trial {trial}] size={width}x{height} rot={rotation} top={offset_top} inv={invert} speed={speed/1_000_000:.0f}MHz cs={cs} dc={dc} rst={rst} bl={backlight} no_rst={no_rst} no_bl={no_backlight}"
                                            )
                                            try:
                                                display = _init_display(args)
                                                img = Image.new('RGB', (display.width, display.height), color=(255, 0, 0))
                                                draw = ImageDraw.Draw(img)
                                                try:
                                                    font = ImageFont.truetype(
                                                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
                                                    )
                                                except Exception:
                                                    font = ImageFont.load_default()

                                                draw.rectangle([0, 0, display.width, 34], fill=(0, 0, 0))
                                                draw.text(
                                                    (5, 6),
                                                    f"{width}x{height} r{rotation} t{offset_top} cs{cs} dc{dc} rst{int(not no_rst)}",
                                                    font=font,
                                                    fill=(255, 255, 255),
                                                )
                                                display.display(img)
                                                time.sleep(2)
                                            except Exception as e:
                                                print(f"  init/display failed: {e}")

def test_display(args: argparse.Namespace) -> bool:
    """Test ST7789V3 display with various patterns and colors"""
    
    print("Initializing ST7789V3 display...")
    print("ST7789V3 Driver - Enhanced version with built-in charge pump")
    
    try:
        display = _init_display(args)
        
        print("✓ ST7789V3 display initialized successfully!")
        print(f"  Resolution: {display.width}x{display.height}")
        print(f"  Driver: ST7789V3 (Enhanced)")
        print(f"  SPI Speed: {args.speed/1_000_000:.0f} MHz")
        if args.offset_left is not None or args.offset_top is not None:
            print(f"  Offset: left={args.offset_left or 0}, top={args.offset_top or 0}")
        
    except Exception as e:
        print(f"✗ Failed to initialize ST7789V3 display: {e}")
        print("\nST7789V3 Troubleshooting:")
        print("1. Check SPI is enabled: sudo raspi-config → Interface Options → SPI")
        print("2. Verify ST7789V3 wiring connections:")
        print("   - VCC  → 3.3V (Pin 1 or 17)")
        print("   - GND  → GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39)")
        print("   - SCL  → SCLK (GPIO 11, Pin 23)")
        print("   - SDA  → MOSI (GPIO 10, Pin 19)")
        print(f"   - RES  → GPIO {args.rst} (configurable)")
        print(f"   - DC   → GPIO {args.dc} (configurable)")
        print("   - CS   → CE0 (GPIO 8, Pin 24)  [or CE1 (GPIO 7, Pin 26)]")
        print(f"   - BLK  → GPIO {args.backlight} (configurable)")
        print("3. Check GPIO pins match your ST7789V3 module")
        print("4. Verify 3.3V power supply (ST7789V3 uses internal charge pump)")
        return False
    
    # Get display dimensions
    WIDTH = display.width
    HEIGHT = display.height
    
    print("\n" + "="*50)
    print("Starting Display Tests")
    print("="*50)
    
    # Test 0: Initial clear and white screen to verify display is working
    print("\n[Test 0/6] Initial display test (WHITE screen)...")
    print("  If you see a WHITE screen, the display is working!")
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(255, 255, 255))
    display.display(img)
    time.sleep(2)
    print("  ✓ If screen is white, display is functional")
    
    # Test 1: Solid Colors
    print("\n[Test 1/6] Testing solid colors...")
    colors = [
        ("RED", (255, 0, 0)),
        ("GREEN", (0, 255, 0)),
        ("BLUE", (0, 0, 255)),
        ("YELLOW", (255, 255, 0)),
        ("CYAN", (0, 255, 255)),
        ("MAGENTA", (255, 0, 255)),
        ("WHITE", (255, 255, 255)),
        ("BLACK", (0, 0, 0))
    ]
    
    for name, color in colors:
        print(f"  Displaying {name}...")
        img = Image.new('RGB', (WIDTH, HEIGHT), color=color)
        display.display(img)
        time.sleep(0.5)
    
    print("✓ Color test complete")
    
    # Test 2: Gradient
    print("\n[Test 2/6] Testing gradient...")
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    for x in range(WIDTH):
        color = int((x / WIDTH) * 255)
        draw.line([(x, 0), (x, HEIGHT)], fill=(color, 0, 255 - color))
    
    display.display(img)
    time.sleep(2)
    print("✓ Gradient test complete")
    
    # Test 3: Geometric Shapes
    print("\n[Test 3/6] Testing geometric shapes...")
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Circle
    draw.ellipse([10, 10, 100, 100], fill=(255, 0, 0), outline=(255, 255, 255))
    # Rectangle
    draw.rectangle([120, 10, 230, 100], fill=(0, 255, 0), outline=(255, 255, 255))
    # Triangle (polygon)
    draw.polygon([(60, 120), (10, 220), (110, 220)], fill=(0, 0, 255), outline=(255, 255, 255))
    # Line
    draw.line([(120, 120), (230, 220)], fill=(255, 255, 0), width=5)
    
    display.display(img)
    time.sleep(2)
    print("✓ Shapes test complete")
    
    # Test 4: Text Display
    print("\n[Test 4/6] Testing text display...")
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 50, 100))
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fallback to default if not available
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw.text((10, 10), "ST7789V3 Display", font=font_large, fill=(255, 255, 255))
    draw.text((10, 50), "Test Successful!", font=font_small, fill=(0, 255, 0))
    draw.text((10, 80), f"Resolution: {WIDTH}x{HEIGHT}", font=font_small, fill=(255, 255, 0))
    draw.text((10, 110), "Raspberry Pi 3", font=font_small, fill=(255, 100, 255))
    draw.text((10, 140), "Driver: ST7789V3", font=font_small, fill=(100, 255, 255))
    draw.text((10, HEIGHT - 30), "SPI Display Working!", font=font_small, fill=(0, 255, 255))
    
    display.display(img)
    time.sleep(3)
    print("✓ Text test complete")
    
    # Test 5: Pattern
    print("\n[Test 5/6] Testing checkerboard pattern...")
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    square_size = 20
    for y in range(0, HEIGHT, square_size):
        for x in range(0, WIDTH, square_size):
            if (x // square_size + y // square_size) % 2 == 0:
                draw.rectangle([x, y, x + square_size, y + square_size], fill=(255, 255, 255))
    
    display.display(img)
    time.sleep(2)
    print("✓ Pattern test complete")
    
    # Test 6: Animation
    print("\n[Test 6/6] Testing animation (bouncing ball)...")
    ball_x, ball_y = WIDTH // 2, HEIGHT // 2
    ball_dx, ball_dy = 5, 3
    ball_radius = 15
    
    for _ in range(50):  # 50 frames
        img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 50))
        draw = ImageDraw.Draw(img)
        
        # Draw ball
        draw.ellipse([ball_x - ball_radius, ball_y - ball_radius,
                     ball_x + ball_radius, ball_y + ball_radius],
                    fill=(255, 50, 50), outline=(255, 255, 255))
        
        # Update position
        ball_x += ball_dx
        ball_y += ball_dy
        
        # Bounce off edges
        if ball_x <= ball_radius or ball_x >= WIDTH - ball_radius:
            ball_dx = -ball_dx
        if ball_y <= ball_radius or ball_y >= HEIGHT - ball_radius:
            ball_dy = -ball_dy
        
        display.display(img)
        time.sleep(0.02)
    
    print("✓ Animation test complete")
    
    # Final message
    print("\n" + "="*50)
    print("All tests completed successfully!")
    print("="*50)
    
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 100, 0))
    draw = ImageDraw.Draw(img)
    draw.text((WIDTH//2 - 80, HEIGHT//2 - 20), "ALL TESTS", font=font_large, fill=(255, 255, 255))
    draw.text((WIDTH//2 - 60, HEIGHT//2 + 20), "PASSED!", font=font_large, fill=(0, 255, 0))
    display.display(img)
    
    return True


def quick_test(args: argparse.Namespace) -> bool:
    """Quick test - just display a simple message on ST7789V3"""
    print("Running ST7789V3 quick test...")
    
    try:
        display = _init_display(args)
        
        img = Image.new('RGB', (display.width, display.height), color=(0, 0, 255))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, display.height//2 - 40), "ST7789V3", font=font, fill=(255, 255, 0))
        draw.text((10, display.height//2 + 10), "DISPLAY OK!", font=font, fill=(255, 255, 255))
        display.display(img)
        
        print("✓ ST7789V3 quick test successful!")
        return True
        
    except Exception as e:
        print(f"✗ ST7789V3 quick test failed: {e}")
        return False


if __name__ == "__main__":
    parser = _build_arg_parser()
    args = parser.parse_args()

    print("=" * 50)
    print("ST7789/ST7789V3 Display Test Script")
    print("=" * 50)
    backlight_label = "none" if args.no_backlight else str(_phys_to_bcm(args.backlight_phys) if args.backlight_phys is not None else args.backlight)
    dc_label = str(_phys_to_bcm(args.dc_phys)) if args.dc_phys is not None else str(args.dc)
    rst_label = str(_phys_to_bcm(args.rst_phys)) if args.rst_phys is not None else str(args.rst)
    print(
        f"Using (BCM): rotation={args.rotation}, port={args.port}, cs={args.cs}, dc={dc_label}, rst={rst_label}, backlight={backlight_label}, speed={args.speed}"
    )
    if args.width and args.height:
        print(f"Panel override: {args.width}x{args.height}")
    if args.offset_left is not None or args.offset_top is not None:
        print(f"Offset: left={args.offset_left or 0}, top={args.offset_top or 0}")

    if args.scan:
        scan_for_working_config(args)
    elif args.quick:
        quick_test(args)
    else:
        test_display(args)
