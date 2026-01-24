#!/usr/bin/env python3
"""
Display Check-in/Check-out Times on ST7789 Screen
Shows real-time attendance status from the face recognition system
"""

import time
import argparse
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os
import csv
import json
from attendance_tracker import AttendanceTracker

from st7789_raw_driver import RawST7789, phys_to_bcm

# Display configuration
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 240

# Colors
BG_COLOR = (0, 30, 60)
HEADER_BG = (0, 50, 100)
TEXT_COLOR = (255, 255, 255)
STATUS_IN_COLOR = (46, 204, 113)  # Green
STATUS_OUT_COLOR = (149, 165, 166)  # Gray
TIME_COLOR = (255, 255, 100)
BORDER_COLOR = (100, 150, 200)


class AttendanceDisplay:
    """Display attendance information on ST7789 screen"""
    
    def __init__(self, args: argparse.Namespace):
        """Initialize display"""
        print("Initializing ST7789 display...")

        # Prefer the raw backend (this matches the init that worked for your panel).
        # Defaults are the known-good wiring:
        #   CS=CE0, DC=physical pin 22 (GPIO25), RST=physical pin 18 (GPIO24)
        # Backlight can be tied to 3.3V and does not need GPIO control.
        try:
            dc_gpio = phys_to_bcm(args.dc_phys) if args.dc_phys is not None else args.dc
            rst_gpio = None if args.no_rst else (phys_to_bcm(args.rst_phys) if args.rst_phys is not None else args.rst)
            backlight_gpio = None
            if not args.no_backlight:
                backlight_gpio = (
                    phys_to_bcm(args.backlight_phys) if args.backlight_phys is not None else args.backlight
                )

            self.display = RawST7789(
                port=args.port,
                cs=args.cs,
                dc=dc_gpio,
                rst=rst_gpio,
                backlight=backlight_gpio,
                speed=args.speed,
                spi_mode=args.spi_mode,
                width=args.width,
                height=args.height,
                offset_left=args.offset_left,
                offset_top=args.offset_top,
                rotation=args.rotation,
                invert=args.invert,
            )
            self._raw_backend = True
        except Exception as e:
            print(f"[WARNING] Raw ST7789 init failed: {e}")
            print("[INFO] Falling back to `st7789` library...")
            import st7789

            self.display = st7789.ST7789(
                width=args.width,
                height=args.height,
                rotation=args.rotation,
                port=args.port,
                cs=args.cs,
                dc=(phys_to_bcm(args.dc_phys) if args.dc_phys is not None else args.dc),
                rst=(phys_to_bcm(args.rst_phys) if args.rst_phys is not None else args.rst),
                backlight=(
                    None
                    if args.no_backlight
                    else (phys_to_bcm(args.backlight_phys) if args.backlight_phys is not None else args.backlight)
                ),
                spi_speed_hz=args.speed,
                offset_left=args.offset_left,
                offset_top=args.offset_top,
                invert=args.invert,
            )
            self._raw_backend = False
        
        # Load fonts
        try:
            self.font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            self.font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            self.font_info = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            self.font_time = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
            self.font_flash = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        except:
            self.font_title = ImageFont.load_default()
            self.font_name = ImageFont.load_default()
            self.font_info = ImageFont.load_default()
            self.font_time = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_flash = ImageFont.load_default()
        
        self.tracker = AttendanceTracker()
        print("✓ Display initialized")

        # Make it obvious immediately if pixels are updating.
        try:
            if getattr(self, "_raw_backend", False) and hasattr(self.display, "fill_rgb565"):
                # Blue-ish screen in RGB565
                self.display.fill_rgb565(0x00, 0x1F)
        except Exception:
            pass

        # UI state
        self._prev_status: dict[str, dict] = {}
        self._flash_until: float = 0.0
        self._flash_text: str | None = None
        self._current_user: str | None = None
        self._last_event_seen_ts: float = 0.0

        # If the tracker supports last_event.json, prefer it to avoid duplicate flashes.
        self._event_sync_path = getattr(self.tracker, "last_event_file", None)

    def _read_last_event(self) -> dict | None:
        try:
            path = getattr(self.tracker, "last_event_file", None)
            if not path or not os.path.exists(path):
                return None
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return None
            return data
        except Exception:
            return None

    def _parse_hms(self, t: str | None) -> datetime | None:
        if not t:
            return None
        try:
            # Stored as HH:MM:SS
            dt = datetime.strptime(t, "%H:%M:%S")
            now = datetime.now()
            return dt.replace(year=now.year, month=now.month, day=now.day)
        except Exception:
            return None

    def _format_duration(self, seconds: int) -> str:
        if seconds < 0:
            seconds = 0
        minutes = seconds // 60
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"

    def _day_total_str(self, info: dict) -> str:
        # Prefer stored Excel duration when available.
        total = info.get("duration")
        if total and str(total).strip() not in {"N/A", "None"}:
            return str(total)

        time_in = self._parse_hms(info.get("check_in_time"))
        if not time_in:
            return "0h 0m"

        time_out = self._parse_hms(info.get("check_out_time"))
        end = time_out if time_out else datetime.now()
        return self._format_duration(int((end - time_in).total_seconds()))

    def _pick_display_user(self, user_status: dict[str, dict]) -> str | None:
        if not user_status:
            return None

        # If the currently displayed user is still present, keep it.
        if self._current_user and self._current_user in user_status:
            return self._current_user

        # Otherwise, show the most recent activity.
        def sort_key(item):
            info = item[1] or {}
            t = self._parse_hms(info.get("last_time"))
            return t.timestamp() if t else 0

        name, _ = max(user_status.items(), key=sort_key)
        return name

    def _detect_event_flash(self, prev: dict[str, dict], curr: dict[str, dict]) -> str | None:
        # Detect transitions and return flash text.
        events: list[tuple[float, str]] = []

        names = set(prev.keys()) | set(curr.keys())
        for name in names:
            p = prev.get(name)
            c = curr.get(name)

            p_status = (p or {}).get("status")
            c_status = (c or {}).get("status")

            # New user appeared today with a check-in.
            if p is None and c_status == "IN":
                t = self._parse_hms((c or {}).get("check_in_time"))
                # events.append(((t.timestamp() if t else time.time()), ""))
                continue

            # OUT -> IN (re-check-in after clearing last out)
            if p_status == "OUT" and c_status == "IN":
                t = self._parse_hms((c or {}).get("check_in_time"))
                # events.append(((t.timestamp() if t else time.time()), ""))
                continue

            # IN -> OUT
            if p_status == "IN" and c_status == "OUT":
                t = self._parse_hms((c or {}).get("check_out_time"))
                # events.append(((t.timestamp() if t else time.time()), "CHECK OUT SUCCESS"))
                continue

        if not events:
            return None

        events.sort(key=lambda x: x[0], reverse=True)
        return events[0][1]
    
    def draw_header(self, draw):
        """Draw header section"""
        # Header background
        draw.rectangle([0, 0, DISPLAY_WIDTH, 35], fill=HEADER_BG)
        
        # Title
        draw.text((10, 8), "Attendance", font=self.font_title, fill=TEXT_COLOR)
        
        # Current time
        current_time = datetime.now().strftime("%H:%M")
        draw.text((DISPLAY_WIDTH - 60, 10), current_time, font=self.font_info, fill=TIME_COLOR)
        
        # Border line
        draw.line([0, 35, DISPLAY_WIDTH, 35], fill=BORDER_COLOR, width=2)

    def _draw_flash(self, draw, action_text: str):
        draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=(0, 0, 0))

        # Two-line centered message for small LCD
        # Defensive: if any caller accidentally passes "... SUCCESS ...", strip it.
        line1 = (action_text or "").replace("SUCCESS", "").replace("SUCCESS", "")
        line1 = " ".join(line1.split())
        line2 = "SUCCESS"

        # Pick a font size that fits the screen width.
        flash_font = self.font_flash
        try:
            for size in (28, 24, 20, 18):
                candidate = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
                b2 = draw.textbbox((0, 0), line2, font=candidate)
                w2 = b2[2] - b2[0]
                if w2 <= DISPLAY_WIDTH - 20:
                    flash_font = candidate
                    break
        except Exception:
            pass

        b1 = draw.textbbox((0, 0), line1, font=flash_font)
        w1 = b1[2] - b1[0]
        h1 = b1[3] - b1[1]

        b2 = draw.textbbox((0, 0), line2, font=flash_font)
        w2 = b2[2] - b2[0]
        h2 = b2[3] - b2[1]

        gap = 10
        total_h = h1 + gap + h2
        y0 = (DISPLAY_HEIGHT - total_h) // 2

        draw.text(((DISPLAY_WIDTH - w1) // 2, y0), line1, font=flash_font, fill=TEXT_COLOR)
        draw.text(((DISPLAY_WIDTH - w2) // 2, y0 + h1 + gap), line2, font=flash_font, fill=TEXT_COLOR)

    def _draw_single_user(self, draw, name: str, info: dict):
        # Background
        draw.rectangle([0, 35, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=BG_COLOR)

        status = info.get("status", "OUT")
        color = STATUS_IN_COLOR if status == "IN" else STATUS_OUT_COLOR

        # Name
        draw.text((10, 48), name[:18], font=self.font_title, fill=TEXT_COLOR)
        # Status badge
        draw.rectangle([10, 78, 110, 98], fill=color)
        draw.text((16, 80), status, font=self.font_small, fill=(0, 0, 0))

        # Times
        time_in = info.get("check_in_time") or "--:--:--"
        time_out = info.get("check_out_time") or "--:--:--"
        total = self._day_total_str(info)

        draw.text((10, 110), f"Time IN : {time_in}", font=self.font_info, fill=TEXT_COLOR)
        draw.text((10, 132), f"Time OUT: {time_out}", font=self.font_info, fill=TEXT_COLOR)
        draw.text((10, 154), f"Total  : {total}", font=self.font_info, fill=TIME_COLOR)

        # Footer clock
        update_time = datetime.now().strftime("%H:%M:%S")
        draw.text((10, DISPLAY_HEIGHT - 18), update_time, font=self.font_small, fill=(120, 120, 120))
    
    def update_display(self):
        """Update display with current attendance data"""
        # Create new image
        img = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Prefer event-driven sync: show CHECK IN/OUT success immediately when recorded.
        last_event = self._read_last_event()
        if last_event and last_event.get('event') in {'CHECK_IN', 'CHECK_OUT'}:
            try:
                evt_ts = float(last_event.get('ts') or 0.0)
            except Exception:
                evt_ts = 0.0

            if evt_ts > self._last_event_seen_ts:
                self._last_event_seen_ts = evt_ts
                self._current_user = str(last_event.get('name') or '') or self._current_user

                action = "CHECK IN" if last_event.get('event') == 'CHECK_IN' else "CHECK OUT"
                self._draw_flash(draw, action)
                self.display.display(img)

                # Keep the splash visible for a full 2 seconds.
                time.sleep(2.0)

                # After splash, fall through and render the normal screen immediately.
                img = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=BG_COLOR)
                draw = ImageDraw.Draw(img)
                self._flash_text = None
                self._flash_until = 0.0

        # Get user status
        user_status = self.tracker.get_user_status()

        # If we just handled a real event, don't also trigger the old transition flash.
        event_sync_available = bool(self._event_sync_path)
        if event_sync_available:
            self._prev_status = user_status
        else:
            # Detect check-in/out transitions and trigger flash (legacy fallback)
            flash = self._detect_event_flash(self._prev_status, user_status)
            if flash:
                # Map legacy messages to our two-line splash format
                action = "CHECK IN" if "CHECK IN" in flash else "CHECK OUT"
                self._flash_text = action
                self._flash_until = time.time() + 2.0

            self._prev_status = user_status

        # If flash active, render it full-screen
        if self._flash_text and time.time() < self._flash_until:
            self._draw_flash(draw, self._flash_text)
            self.display.display(img)
            return

        # Normal screen
        self.draw_header(draw)

        name = self._pick_display_user(user_status)
        self._current_user = name

        if not name:
            draw.text(
                (DISPLAY_WIDTH // 2 - 50, DISPLAY_HEIGHT // 2),
                "No check-ins yet",
                font=self.font_info,
                fill=(150, 150, 150),
            )
        else:
            self._draw_single_user(draw, name, user_status.get(name, {}))

        # Update display
        self.display.display(img)
    
    def run(self, update_interval=2):
        """Run display loop"""
        print(f"\nStarting attendance display...")
        print(f"Update interval: {update_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.update_display()
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping display...")
            
            # Show goodbye message
            img = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=(0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((DISPLAY_WIDTH // 2 - 50, DISPLAY_HEIGHT // 2 - 10), 
                     "Display Off", font=self.font_title, fill=TEXT_COLOR)
            self.display.display(img)
            
            print("✓ Display stopped")


def main():
    """Main entry point"""
    print("="*50)
    print("ST7789 Attendance Display")
    print("="*50)

    parser = argparse.ArgumentParser(description="ST7789 Attendance Display")
    parser.add_argument("--update-interval", type=float, default=2.0)

    # SPI
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--cs", type=int, default=0, choices=[0, 1])
    parser.add_argument("--speed", type=int, default=4_000_000)
    parser.add_argument("--spi-mode", type=int, default=0, choices=[0, 1, 2, 3])

    # Panel
    parser.add_argument("--width", type=int, default=240)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--offset-left", type=int, default=0)
    parser.add_argument("--offset-top", type=int, default=0)
    parser.add_argument("--rotation", type=int, default=90, choices=[0, 90, 180, 270])

    inv = parser.add_mutually_exclusive_group()
    inv.add_argument("--invert", dest="invert", action="store_true")
    inv.add_argument("--no-invert", dest="invert", action="store_false")
    parser.set_defaults(invert=True)

    # GPIO
    parser.add_argument("--dc", type=int, default=25, help="BCM GPIO")
    parser.add_argument("--rst", type=int, default=24, help="BCM GPIO")
    parser.add_argument("--no-rst", action="store_true")
    parser.add_argument("--dc-phys", type=int, default=22, help="physical pin for DC (default: 22)")
    parser.add_argument("--rst-phys", type=int, default=18, help="physical pin for RST (default: 18)")

    parser.add_argument("--backlight", type=int, default=18, help="BCM GPIO for BL/BLK")
    parser.add_argument("--backlight-phys", type=int, default=12, help="physical pin for BL/BLK (default: 12)")
    parser.add_argument(
        "--no-backlight",
        action="store_true",
        help="do not control backlight via GPIO (use when BLK is tied to 3.3V)",
    )

    args = parser.parse_args()

    display = AttendanceDisplay(args)
    display.run(update_interval=args.update_interval)


if __name__ == "__main__":
    main()
