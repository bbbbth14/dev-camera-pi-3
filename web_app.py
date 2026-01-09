"""
Web-based GUI Application for Face Recognition System
Works via browser - perfect for headless or remote Raspberry Pi
"""

from flask import Flask, render_template, Response, request, jsonify
import cv2
import threading
import time
from datetime import datetime
import os
import json

from face_detector import FaceDetector
from face_recognizer import FaceRecognizer
from attendance_tracker import AttendanceTracker
from camera_wrapper import Camera
import config

# Try to import ST7789 for LCD display
try:
    import st7789
    from PIL import Image, ImageDraw, ImageFont
    LCD_AVAILABLE = True
    print("[INFO] ST7789 LCD display library loaded")
except Exception as e:
    LCD_AVAILABLE = False
    print(f"[INFO] ST7789 not available - LCD display disabled ({e})")

app = Flask(__name__)

# Global state
class SystemState:
    def __init__(self):
        self.detector = FaceDetector()
        self.recognizer = FaceRecognizer()
        self.tracker = AttendanceTracker()
        self.camera = None
        self.running = False
        self.current_mode = None
        self.logs = []
        self.last_recognition = {}
        self.last_attendance_name = None
        self.last_attendance_at = 0.0
        
        # Enrollment state
        self.enrolling = False
        self.enroll_name = ""
        self.enroll_images = []
        self.enroll_progress = 0
        self.enrollment_success = False
        self.success_message = ""
        self.enrollment_success = False
        self.success_message = ""
        
        # LCD display
        self.lcd_display = None
        self.lcd_thread = None
        self.lcd_running = False
        self.lcd_success_message = None
        self.lcd_success_until = 0
        
        if LCD_AVAILABLE:
            try:
                self.lcd_display = st7789.ST7789(
                    rotation=90,
                    port=0,
                    cs=0,         # CE0 (GPIO 8, Pin 24)
                    dc=25,        # GPIO 25, Pin 22
                    backlight=18, # GPIO 18, Pin 12
                    rst=24,       # GPIO 24, Pin 18
                    spi_speed_hz=80 * 1000000
                )
                # Load fonts - even bigger
                try:
                    self.lcd_font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
                    self.lcd_font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                    self.lcd_font_time = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
                    self.lcd_font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                    self.lcd_font_success = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                except:
                    self.lcd_font_title = ImageFont.load_default()
                    self.lcd_font_name = ImageFont.load_default()
                    self.lcd_font_time = ImageFont.load_default()
                    self.lcd_font_small = ImageFont.load_default()
                
                print("[INFO] LCD display initialized")
            except Exception as e:
                print(f"[WARNING] LCD display initialization failed: {e}")
                self.lcd_display = None
    
    def update_lcd(self):
        """Update LCD display with attendance info"""
        if not self.lcd_display or not self.running or self.current_mode != 'attendance':
            return
        
        try:
            # Create image
            img = Image.new('RGB', (240, 240), color=(0, 30, 60))
            draw = ImageDraw.Draw(img)
            
            # Check if showing success popup
            current_time = time.time()
            if self.lcd_success_message and current_time < self.lcd_success_until:
                # Show SUCCESS popup
                draw.rectangle([0, 0, 240, 240], fill=(0, 100, 0))
                draw.text((30, 70), "SUCCESS!", font=self.lcd_font_success, fill=(255, 255, 255))
                draw.text((20, 120), self.lcd_success_message, font=self.lcd_font_name, fill=(255, 255, 100))
                self.lcd_display.display(img)
                return
            else:
                self.lcd_success_message = None
            
            # Header
            draw.rectangle([0, 0, 240, 38], fill=(0, 50, 100))
            draw.text((8, 8), "Attendance", font=self.lcd_font_time, fill=(255, 255, 255))
            current_time_str = datetime.now().strftime("%H:%M")
            draw.text((155, 10), current_time_str, font=self.lcd_font_time, fill=(255, 255, 100))
            draw.line([0, 38, 240, 38], fill=(100, 150, 200), width=2)
            
            # Get user status
            user_status = self.tracker.get_user_status()
            
            if not user_status:
                draw.text((40, 120), "No users", font=self.lcd_font_name, fill=(150, 150, 150))
            else:
                # Display only 1 user to fit all info.
                # Prefer the last recognized person so the LCD matches the camera event.
                y_pos = 42

                selected = None
                if self.last_attendance_name and (time.time() - self.last_attendance_at) < 60:
                    if self.last_attendance_name in user_status:
                        selected = (self.last_attendance_name, user_status[self.last_attendance_name])

                if selected is None:
                    sorted_users = sorted(
                        user_status.items(),
                        key=lambda x: (x[1].get('last_time') or ''),
                        reverse=True
                    )
                    selected = sorted_users[0]

                name, status_info = selected
                # Card background (fit within 240px screen)
                draw.rectangle([3, y_pos, 237, y_pos + 195],
                             fill=(20, 60, 40), outline=(46, 204, 113), width=3)
                
                # Name (very large)
                draw.text((10, y_pos + 5), name[:8], font=self.lcd_font_name, fill=(255, 255, 255))
                
                # Check IN/OUT status (large text)
                status = status_info.get('status', 'OUT')
                in_time = status_info.get('check_in_time') or 'N/A'
                out_time = status_info.get('check_out_time') or 'N/A'
                
                if status == 'IN':
                    in_time_str = status_info.get('check_in_time', 'N/A')
                    status_text = f"IN: {in_time_str}"
                    status_color = (0, 255, 0)
                    draw.text((10, y_pos + 40), status_text, font=self.lcd_font_time, fill=status_color)
                    
                    # Calculate time since check-in
                    if in_time_str != 'N/A':
                        try:
                            in_time = datetime.strptime(in_time_str, "%H:%M:%S")
                            now = datetime.now()
                            in_time = in_time.replace(year=now.year, month=now.month, day=now.day)
                            duration = now - in_time
                            hours = duration.seconds // 3600
                            minutes = (duration.seconds % 3600) // 60
                            total_text = f"TOTAL: {hours}h {minutes}m"
                            draw.text((10, y_pos + 70), total_text, font=self.lcd_font_time, fill=(255, 255, 150))
                        except:
                            pass
                else:
                    # Status is OUT - show both IN and OUT times if available
                    # IN time
                    draw.text((10, y_pos + 40), f"IN: {in_time}", font=self.lcd_font_time, fill=(100, 200, 255))
                    # OUT time
                    if out_time != 'N/A':
                        draw.text((10, y_pos + 67), f"OUT: {out_time}", font=self.lcd_font_time, fill=(255, 150, 150))
                        
                        # Calculate total time
                        if in_time != 'N/A':
                            try:
                                in_dt = datetime.strptime(in_time, "%H:%M:%S")
                                out_dt = datetime.strptime(out_time, "%H:%M:%S")
                                now = datetime.now()
                                in_dt = in_dt.replace(year=now.year, month=now.month, day=now.day)
                                out_dt = out_dt.replace(year=now.year, month=now.month, day=now.day)
                                duration = out_dt - in_dt
                                hours = duration.seconds // 3600
                                minutes = (duration.seconds % 3600) // 60
                                total_text = f"TOTAL: {hours}h {minutes}m"
                                draw.text((10, y_pos + 94), total_text, font=self.lcd_font_time, fill=(255, 255, 150))
                            except:
                                pass
                    
                    # LATE/ON TIME indicator below Total (if has first check-in)
                    first_checkin = status_info.get('first_check_in')
                    if first_checkin:
                        try:
                            checkin_time = datetime.strptime(first_checkin, "%H:%M:%S")
                            cutoff_time = datetime.strptime("08:00:00", "%H:%M:%S")
                            if checkin_time.time() > cutoff_time.time():
                                draw.text((10, y_pos + 121), "STATUS: LATE", font=self.lcd_font_time, fill=(255, 100, 100))
                            else:
                                draw.text((10, y_pos + 121), "STATUS: ON TIME", font=self.lcd_font_time, fill=(100, 255, 100))
                        except:
                            pass
                    
                    # OT indicator
                    is_ot = status_info.get('is_overtime', False)
                    ot_text = "OT: Yes" if is_ot else "OT: No"
                    ot_color = (100, 255, 100)  # Green like STATUS
                    draw.text((10, y_pos + 148), ot_text, font=self.lcd_font_time, fill=ot_color)
                    

                    y_pos += 205
            
            # Update display
            self.lcd_display.display(img)
            
        except Exception as e:
            print(f"[ERROR] LCD update failed: {e}")
    
    def start_lcd_updates(self):
        """Start LCD update thread"""
        if not self.lcd_display or self.lcd_running:
            return
        
        self.lcd_running = True
        
        def lcd_loop():
            while self.lcd_running and self.running and self.current_mode == 'attendance':
                self.update_lcd()
                time.sleep(2)
            
            # Clear display when stopped
            if self.lcd_display:
                try:
                    img = Image.new('RGB', (240, 240), color=(0, 0, 0))
                    draw = ImageDraw.Draw(img)
                    draw.text((60, 110), "Standby Mode", font=self.lcd_font_title, fill=(100, 100, 100))
                    self.lcd_display.display(img)
                except:
                    pass
            self.lcd_running = False
        
        self.lcd_thread = threading.Thread(target=lcd_loop, daemon=True)
        self.lcd_thread.start()
        print("[INFO] LCD update thread started")
        
    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        if len(self.logs) > 100:
            self.logs.pop(0)

state = SystemState()
output_frame = None
lock = threading.Lock()


def generate_frames():
    """Generate video frames for streaming"""
    global output_frame
    
    while True:
        with lock:
            if output_frame is None:
                time.sleep(0.1)
                continue
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', output_frame)
            if not ret:
                continue
            frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        time.sleep(0.03)


def camera_loop():
    """Main camera processing loop"""
    global output_frame
    
    try:
        state.camera = Camera()
        state.add_log("Camera initialized")
        
        frame_count = 0
        
        while state.running or state.enrolling:
            ret, frame = state.camera.read()
            if not ret or frame is None:
                time.sleep(0.1)
                continue
            
            frame_count += 1
            display_frame = frame.copy()
            
            # Enrollment mode
            if state.enrolling:
                if frame_count % 3 == 0:
                    face_locations = state.detector.detect_faces(frame)
                    
                    if len(face_locations) > 0 and len(state.enroll_images) < 3:
                        # Draw rectangle
                        for (x, y, w, h) in face_locations:
                            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                            cv2.putText(display_frame, f"Capturing {len(state.enroll_images)+1}/3", 
                                      (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        # Capture every few frames (faster)
                        if frame_count % 5 == 0:
                            state.enroll_images.append(frame.copy())
                            state.enroll_progress = len(state.enroll_images)
                            
                            if len(state.enroll_images) >= 3:
                                state.add_log(f"✓ Captured 3 images for {state.enroll_name}")
                                # Auto-save and train immediately
                                try:
                                    user_dir = os.path.join(config.IMAGES_DIR, state.enroll_name)
                                    os.makedirs(user_dir, exist_ok=True)
                                    for idx, img in enumerate(state.enroll_images):
                                        filename = f"{state.enroll_name}_{idx+1}.jpg"
                                        filepath = os.path.join(user_dir, filename)
                                        cv2.imwrite(filepath, img)
                                    state.recognizer.train()
                                    state.add_log(f"✓ {state.enroll_name} enrolled successfully")
                                    # Set success notification
                                    state.enrollment_success = True
                                    state.success_message = f"✓ {state.enroll_name} enrolled successfully!"
                                    state.enrolling = False
                                    enrolled_name = state.enroll_name
                                    state.enroll_name = ""
                                    state.enroll_images = []
                                    state.enroll_progress = 0
                                    # Clear notification after 5 seconds
                                    threading.Timer(5.0, lambda: setattr(state, 'enrollment_success', False)).start()
                                except Exception as e:
                                    state.add_log(f"✗ Enrollment failed: {str(e)}")
                    
                    elif len(face_locations) == 0:
                        cv2.putText(display_frame, "No face detected - look at camera", 
                                  (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            
            # Recognition mode
            elif state.running and frame_count % config.PROCESS_EVERY_N_FRAMES == 0:
                face_locations = state.detector.detect_faces(frame)
                
                if len(face_locations) > 0:
                    face_names = state.recognizer.recognize_faces(frame, face_locations)
                    
                    for (x, y, w, h), name in zip(face_locations, face_names):
                        if name != "Unknown":
                            current_time = time.time()
                            
                            if name not in state.last_recognition or \
                               current_time - state.last_recognition[name] > 3.0:
                                
                                state.last_recognition[name] = current_time
                                
                                if state.current_mode == 'attendance':
                                    status = state.tracker.check_in_out(name)
                                    state.last_attendance_name = name
                                    state.last_attendance_at = time.time()
                                    
                                    # Always read current status after toggle
                                    user_status = state.tracker.get_user_status()
                                    
                                    # Log all check-in/out events with times from Excel
                                    if status == 'CHECKED IN':
                                        if name in user_status:
                                            # Always show the FIRST check-in time of the day
                                            check_in_time = user_status[name].get('first_check_in', 'N/A')
                                            log_msg = f"✓ {name}: CHECKED IN at {check_in_time}"
                                        else:
                                            log_msg = f"✓ {name}: CHECKED IN"
                                        state.add_log(log_msg)
                                        print(f"[ATTENDANCE] {log_msg}")
                                    elif status == 'CHECKED OUT':
                                        if name in user_status:
                                            # Show the LAST check-out time
                                            check_out_time = user_status[name].get('check_out_time', 'N/A')
                                            log_msg = f"✓ {name}: CHECKED OUT at {check_out_time}"
                                        else:
                                            log_msg = f"✓ {name}: CHECKED OUT"
                                        state.add_log(log_msg)
                                        print(f"[ATTENDANCE] {log_msg}")
                                    
                                    # Show SUCCESS popup on LCD
                                    state.lcd_success_message = f"{name}"
                                    state.lcd_success_until = time.time() + 3.0
                                    state.update_lcd()
                                else:
                                    state.add_log(f"✓ Access GRANTED: {name}")
                        
                        # Draw rectangle
                        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 3)
                        cv2.putText(display_frame, name, (x, y - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Update output frame
            with lock:
                output_frame = display_frame.copy()
            
            time.sleep(0.01)
            
    except Exception as e:
        state.add_log(f"ERROR: {str(e)}")
    finally:
        if state.camera:
            state.camera.release()


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/status')
def api_status():
    """Get system status"""
    # Get enrolled users from both recognizer and images directory
    enrolled_names = []
    if hasattr(state.recognizer, 'known_names') and state.recognizer.known_names:
        enrolled_names = state.recognizer.known_names
    elif hasattr(state.recognizer, 'known_face_names') and state.recognizer.known_face_names:
        enrolled_names = state.recognizer.known_face_names
    else:
        # Fallback: read from images directory
        if os.path.exists(config.IMAGES_DIR):
            enrolled_names = [d for d in os.listdir(config.IMAGES_DIR) 
                            if os.path.isdir(os.path.join(config.IMAGES_DIR, d))]
    
    enrolled = len(enrolled_names)
    user_status = state.tracker.get_user_status()
    
    return jsonify({
        'running': state.running,
        'enrolling': state.enrolling,
        'mode': state.current_mode,
        'enrolled_users': enrolled,
        'logs': state.logs[-20:],
        'enroll_progress': state.enroll_progress if state.enrolling else 0,
        'enrollment_success': state.enrollment_success,
        'success_message': state.success_message,
        'user_status': user_status,
        'registered_users': enrolled_names
    })


@app.route('/api/start/<mode>')
def api_start(mode):
    """Start recognition in specified mode"""
    if state.running or state.enrolling:
        return jsonify({'success': False, 'message': 'Already running'})
    
    state.current_mode = mode
    state.running = True
    state.add_log(f"Started {mode.upper()} mode")
    
    # Start camera thread if not running
    threading.Thread(target=camera_loop, daemon=True).start()
    
    # Start LCD updates for attendance mode
    if mode == 'attendance':
        state.start_lcd_updates()
    
    return jsonify({'success': True})


@app.route('/api/stop')
def api_stop():
    """Stop recognition"""
    state.running = False
    state.lcd_running = False
    state.current_mode = None
    state.add_log("Stopped")
    time.sleep(0.5)
    
    return jsonify({'success': True})


@app.route('/api/enroll/start', methods=['POST'])
def api_enroll_start():
    """Start enrollment process"""
    if state.running or state.enrolling:
        return jsonify({'success': False, 'message': 'System busy'})
    
    data = request.json
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': 'Name required'})
    
    state.enrolling = True
    state.enroll_name = name
    state.enroll_images = []
    state.enroll_progress = 0
    state.add_log(f"Starting enrollment for {name}")
    
    # Start camera thread if not running
    threading.Thread(target=camera_loop, daemon=True).start()
    
    return jsonify({'success': True})


@app.route('/api/enroll/save')
def api_enroll_save():
    """Save enrolled images and train"""
    if not state.enrolling:
        return jsonify({'success': False, 'message': 'Not enrolling'})
    
    if len(state.enroll_images) < 3:
        return jsonify({'success': False, 'message': f'Need at least 3 images, got {len(state.enroll_images)}'})
    
    try:
        # Create user directory
        user_dir = os.path.join(config.IMAGES_DIR, state.enroll_name)
        os.makedirs(user_dir, exist_ok=True)
        
        # Save images
        for idx, img in enumerate(state.enroll_images):
            filename = f"{state.enroll_name}_{idx+1}.jpg"
            filepath = os.path.join(user_dir, filename)
            cv2.imwrite(filepath, img)
        
        # Retrain
        state.recognizer.train()
        state.add_log(f"✓ Enrolled {state.enroll_name} ({len(state.enroll_images)} images)")
        
        # Reset enrollment state
        state.enrolling = False
        state.enroll_name = ""
        state.enroll_images = []
        state.enroll_progress = 0
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/enroll/cancel')
def api_enroll_cancel():
    """Cancel enrollment"""
    state.enrolling = False
    state.enroll_name = ""
    state.enroll_images = []
    state.enroll_progress = 0
    state.add_log("Enrollment cancelled")
    
    return jsonify({'success': True})


@app.route('/api/user/delete/<name>')
def api_delete_user(name):
    """Delete a registered user"""
    try:
        import shutil
        
        # Remove user directory
        user_dir = os.path.join(config.IMAGES_DIR, name)
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
            state.add_log(f"Deleted user directory: {name}")
        
        # Retrain recognizer
        state.recognizer.train()
        state.add_log(f"✓ Removed user: {name}")
        
        return jsonify({'success': True, 'message': f'User {name} deleted successfully'})
    
    except Exception as e:
        state.add_log(f"ERROR deleting user: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    
    state.add_log("Web server starting...")
    print("\n" + "="*60)
    print("🎥 Face Recognition Web Interface")
    print("="*60)
    print("\nAccess the application at:")
    print("  → http://localhost:5000")
    print("  → http://0.0.0.0:5000")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
