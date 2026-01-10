#!/usr/bin/env python3
"""
Offline Attendance System
Works completely without WiFi/network connection
- Face recognition for check-in/check-out
- Real-time display on ST7789 LCD
- Local data storage
- No internet required
"""

import cv2
import time
import threading
from datetime import datetime
from face_detector import FaceDetector
from face_recognizer import FaceRecognizer
from attendance_tracker import AttendanceTracker
from camera_wrapper import Camera
import config

# Try to import ST7789 for LCD display
try:
    import st7789
    from PIL import Image, ImageDraw, ImageFont
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False
    print("[WARNING] ST7789 display not available")


class OfflineAttendanceSystem:
    """Offline attendance system with LCD display"""
    
    def __init__(self, use_display=True):
        """Initialize the offline attendance system"""
        print("="*60)
        print("OFFLINE ATTENDANCE SYSTEM")
        print("="*60)
        print()
        
        # Initialize components
        print("[INFO] Initializing face detection...")
        self.detector = FaceDetector()
        
        print("[INFO] Initializing face recognition...")
        self.recognizer = FaceRecognizer()
        
        print("[INFO] Initializing attendance tracker...")
        self.tracker = AttendanceTracker()
        
        # Display setup
        self.use_display = use_display and DISPLAY_AVAILABLE
        self.lcd_display = None
        self.display_lock = threading.Lock()
        
        if self.use_display:
            try:
                print("[INFO] Initializing ST7789 display...")
                self.lcd_display = st7789.ST7789(
                    rotation=90,
                    port=0,
                    cs=0,
                    dc=25,
                    backlight=18,
                    rst=24,
                    spi_speed_hz=80 * 1000000
                )
                
                # Load fonts
                try:
                    self.font_large = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                    self.font_medium = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
                    self.font_small = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                except:
                    self.font_large = ImageFont.load_default()
                    self.font_medium = ImageFont.load_default()
                    self.font_small = ImageFont.load_default()
                
                print("[INFO] ✓ LCD display ready")
                self.show_startup_screen()
            except Exception as e:
                print(f"[WARNING] Failed to initialize display: {e}")
                self.use_display = False
        
        # Recognition state
        self.frame_count = 0
        self.last_recognition = {}
        self.recent_events = []
        
        print()
        print("✓ System ready - WiFi not required")
        print("="*60)
        print()
    
    def show_startup_screen(self):
        """Show startup message on LCD"""
        if not self.use_display:
            return
        
        with self.display_lock:
            img = Image.new('RGB', (240, 240), color=(0, 50, 100))
            draw = ImageDraw.Draw(img)
            
            draw.text((20, 80), "OFFLINE", font=self.font_large, fill=(255, 255, 255))
            draw.text((20, 110), "ATTENDANCE", font=self.font_large, fill=(255, 255, 255))
            draw.text((50, 160), "Ready", font=self.font_medium, fill=(100, 255, 100))
            
            self.lcd_display.display(img)
    
    def update_lcd_display(self, name=None, action=None, status="READY"):
        """Update LCD display with current status"""
        if not self.use_display:
            return
        
        try:
            with self.display_lock:
                # Colors
                bg_color = (0, 30, 60)
                header_bg = (0, 50, 100)
                success_color = (46, 204, 113)
                error_color = (231, 76, 60)
                text_color = (255, 255, 255)
                time_color = (255, 255, 100)
                
                # Create image
                img = Image.new('RGB', (240, 240), color=bg_color)
                draw = ImageDraw.Draw(img)
                
                # Header
                draw.rectangle([0, 0, 240, 40], fill=header_bg)
                draw.text((10, 8), "ATTENDANCE", font=self.font_medium, fill=text_color)
                
                # Current time
                current_time = datetime.now().strftime("%H:%M:%S")
                draw.text((150, 12), current_time, font=self.font_small, fill=time_color)
                
                # Status section
                y_pos = 50
                
                if name and action:
                    # Show recognition result
                    if action == "CHECK_IN":
                        status_color = success_color
                        status_text = "CHECK IN"
                    elif action == "CHECK_OUT":
                        status_color = success_color
                        status_text = "CHECK OUT"
                    else:
                        status_color = error_color
                        status_text = "COOLDOWN"
                    
                    # Status badge
                    draw.rectangle([10, y_pos, 230, y_pos + 40], 
                                  fill=status_color, outline=(255, 255, 255), width=2)
                    draw.text((60, y_pos + 10), status_text, 
                             font=self.font_medium, fill=(255, 255, 255))
                    
                    y_pos += 50
                    
                    # Name
                    draw.text((10, y_pos), f"Name: {name}", 
                             font=self.font_small, fill=text_color)
                    y_pos += 25
                    
                    # Time
                    event_time = datetime.now().strftime("%H:%M:%S")
                    draw.text((10, y_pos), f"Time: {event_time}", 
                             font=self.font_small, fill=time_color)
                    y_pos += 30
                else:
                    # Ready status
                    draw.text((60, 100), "READY", font=self.font_large, 
                             fill=success_color)
                    draw.text((30, 135), "Waiting for face...", font=self.font_small, 
                             fill=(150, 150, 150))
                
                # Recent events (last 3)
                if self.recent_events:
                    y_pos = 155
                    draw.text((10, y_pos), "Recent:", font=self.font_small, 
                             fill=(150, 150, 150))
                    y_pos += 20
                    
                    for event in self.recent_events[-3:]:
                        event_text = f"{event['time']} {event['name']}"
                        if len(event_text) > 22:
                            event_text = event_text[:22] + "..."
                        draw.text((10, y_pos), event_text, font=self.font_small, 
                                 fill=(200, 200, 200))
                        y_pos += 18
                        if y_pos > 220:
                            break
                
                # Update display
                self.lcd_display.display(img)
        
        except Exception as e:
            print(f"[WARNING] Display update failed: {e}")
    
    def process_recognition(self, name: str, confidence: float):
        """Process recognized face and update attendance"""
        current_time = time.time()
        
        # Avoid duplicate processing within 2 seconds
        if name in self.last_recognition:
            if current_time - self.last_recognition[name] < 2.0:
                return
        
        self.last_recognition[name] = current_time
        
        # Get current user status to determine if should check in or out
        user_status = self.tracker.get_user_status()
        current_status = user_status.get(name, {}).get('status', 'OUT')
        
        # Check if can process (not in cooldown)
        if self.tracker.can_checkin(name):
            # Determine action based on current status
            if current_status == 'OUT':
                # Person is OUT, so CHECK IN
                self.tracker.record_event(name, 'CHECK_IN', confidence)
                action = "CHECK_IN"
                event_action = 'IN'
                print(f"\n✓ CHECK-IN: {name} (Confidence: {confidence:.2f})")
            else:
                # Person is IN, so CHECK OUT
                self.tracker.record_event(name, 'CHECK_OUT', confidence)
                action = "CHECK_OUT"
                event_action = 'OUT'
                print(f"\n✓ CHECK-OUT: {name} (Confidence: {confidence:.2f})")
            
            # Add to recent events
            event = {
                'name': name,
                'time': datetime.now().strftime("%H:%M"),
                'action': event_action
            }
            self.recent_events.append(event)
            
            # Update LCD
            self.update_lcd_display(name, action)
            
        else:
            # In cooldown period
            remaining = self.tracker.get_cooldown_remaining(name)
            minutes = remaining // 60
            seconds = remaining % 60
            
            print(f"\n⏳ {name} - Cooldown: {minutes}m {seconds}s")
            
            # Show cooldown on LCD
            self.update_lcd_display(name, "COOLDOWN")
        
        # Return to ready after 3 seconds
        time.sleep(3)
        self.update_lcd_display()
    
    def run(self):
        """Run the offline attendance system"""
        print("[INFO] Starting offline attendance system...")
        print("[INFO] No WiFi required - all data stored locally")
        print("[INFO] Press 'q' to quit")
        print()
        
        # Update display to ready state
        self.update_lcd_display()
        
        # Initialize camera
        camera = Camera(config.CAMERA_WIDTH, config.CAMERA_HEIGHT, 
                       config.USE_PI_CAMERA, preview=True)
        
        if not camera.isOpened():
            print("[ERROR] Failed to open camera")
            return
        
        # Create OpenCV window for camera display
        show_opencv_window = True
        window_name = "Offline Attendance (Press 'q' to quit)"
        
        # Try to create window, but don't fail if we can't (headless/SSH mode)
        try:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 800, 600)
            print("[INFO] OpenCV window created")
        except Exception as e:
            print(f"[INFO] Cannot create OpenCV window (headless mode): {e}")
            print("[INFO] Running without camera preview")
            show_opencv_window = False
        
        try:
            while True:
                # Capture frame
                ret, frame = camera.read()
                
                if not ret or frame is None:
                    print("[ERROR] Failed to capture frame")
                    break
                
                self.frame_count += 1
                display_frame = frame.copy()
                
                # Process every Nth frame for performance
                if self.frame_count % config.PROCESS_EVERY_N_FRAMES == 0:
                    # Detect faces
                    faces = self.detector.detect_faces(frame)
                    
                    if len(faces) > 0:
                        # Recognize faces (returns list of names)
                        results = self.recognizer.recognize_faces(frame, faces)
                        
                        # Draw and process results
                        labels = []
                        for i, name in enumerate(results):
                            # Use a fixed confidence since recognizer doesn't return it
                            confidence = 0.85  # Default confidence
                            label = f"{name}"
                            labels.append(label)
                            
                            # Process recognized faces
                            if name != "Unknown":
                                self.process_recognition(name, confidence)
                        
                        # Draw bounding boxes
                        display_frame = self.detector.draw_faces(
                            display_frame, faces, labels)
                
                # Add overlay info
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cv2.putText(display_frame, "OFFLINE MODE", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, timestamp, 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Events: {len(self.recent_events)}", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # Show frame only if window is available
                if show_opencv_window:
                    cv2.imshow(window_name, display_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("\n[INFO] Shutting down...")
                        break
                else:
                    # Headless mode - just check for Ctrl+C
                    import time
                    time.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\n[INFO] Interrupted by user")
        
        finally:
            # Cleanup
            if show_opencv_window:
                cv2.destroyAllWindows()
            camera.release()
            
            # Show shutdown on LCD
            if self.use_display:
                with self.display_lock:
                    img = Image.new('RGB', (240, 240), color=(0, 0, 0))
                    draw = ImageDraw.Draw(img)
                    draw.text((50, 100), "SYSTEM", font=self.font_large, 
                             fill=(255, 255, 255))
                    draw.text((70, 130), "OFF", font=self.font_large, 
                             fill=(255, 255, 255))
                    self.lcd_display.display(img)
            
            print("[INFO] System stopped")
            print(f"[INFO] Total events recorded: {len(self.recent_events)}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Offline Attendance System - No WiFi Required'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Disable ST7789 LCD display'
    )
    
    args = parser.parse_args()
    
    # Create and run system
    system = OfflineAttendanceSystem(use_display=not args.no_display)
    system.run()


if __name__ == "__main__":
    main()
