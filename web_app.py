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
        
        # Enrollment state
        self.enrolling = False
        self.enroll_name = ""
        self.enroll_images = []
        self.enroll_progress = 0
        self.enrollment_success = False
        self.success_message = ""
        self.enrollment_success = False
        self.success_message = ""
        
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
                                    state.add_log(f"✓ {name}: {status}")
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
    
    return jsonify({'success': True})


@app.route('/api/stop')
def api_stop():
    """Stop recognition"""
    state.running = False
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
