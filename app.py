"""
GUI Application for Face Recognition System
A user-friendly graphical interface for the face recognition attendance system
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import cv2
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime
import os
import sys

from face_detector import FaceDetector
from face_recognizer import FaceRecognizer
from attendance_tracker import AttendanceTracker
from camera_wrapper import Camera
import config


class FaceRecognitionApp:
    """GUI Application for Face Recognition System"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Attendance System")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')
        
        # System components
        self.detector = FaceDetector()
        self.recognizer = FaceRecognizer()
        self.tracker = AttendanceTracker()
        self.camera = None
        
        # Running state
        self.running = False
        self.current_mode = None
        self.camera_thread = None
        self.current_frame = None
        
        # UI setup
        self.setup_ui()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Title
        title_frame = tk.Frame(self.root, bg='#34495e', height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🎥 Face Recognition System",
            font=('Arial', 20, 'bold'),
            bg='#34495e',
            fg='white'
        )
        title_label.pack(pady=10)
        
        # Main container
        main_container = tk.Frame(self.root, bg='#2c3e50')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side - Camera feed
        left_frame = tk.Frame(main_container, bg='#34495e', relief=tk.RAISED, borderwidth=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        camera_label = tk.Label(left_frame, text="Camera Feed", font=('Arial', 12, 'bold'), 
                               bg='#34495e', fg='white')
        camera_label.pack(pady=5)
        
        self.video_label = tk.Label(left_frame, bg='black')
        self.video_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Status bar under camera
        self.status_label = tk.Label(
            left_frame,
            text="Ready",
            font=('Arial', 10),
            bg='#2ecc71',
            fg='white',
            height=2
        )
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Right side - Controls and logs
        right_frame = tk.Frame(main_container, bg='#34495e', width=350, relief=tk.RAISED, borderwidth=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Control buttons
        control_label = tk.Label(right_frame, text="Controls", font=('Arial', 12, 'bold'),
                                bg='#34495e', fg='white')
        control_label.pack(pady=10)
        
        # Attendance Mode Button
        self.btn_attendance = tk.Button(
            right_frame,
            text="📋 Start Attendance Mode",
            font=('Arial', 12, 'bold'),
            bg='#3498db',
            fg='white',
            activebackground='#2980b9',
            activeforeground='white',
            cursor='hand2',
            height=2,
            command=lambda: self.toggle_mode('attendance')
        )
        self.btn_attendance.pack(fill=tk.X, padx=15, pady=5)
        
        # Access Control Mode Button
        self.btn_access = tk.Button(
            right_frame,
            text="🔐 Start Access Control",
            font=('Arial', 12, 'bold'),
            bg='#9b59b6',
            fg='white',
            activebackground='#8e44ad',
            activeforeground='white',
            cursor='hand2',
            height=2,
            command=lambda: self.toggle_mode('access')
        )
        self.btn_access.pack(fill=tk.X, padx=15, pady=5)
        
        # Enroll Face Button
        self.btn_enroll = tk.Button(
            right_frame,
            text="👤 Enroll New Face",
            font=('Arial', 12, 'bold'),
            bg='#e67e22',
            fg='white',
            activebackground='#d35400',
            activeforeground='white',
            cursor='hand2',
            height=2,
            command=self.enroll_face
        )
        self.btn_enroll.pack(fill=tk.X, padx=15, pady=5)
        
        # Stop Button
        self.btn_stop = tk.Button(
            right_frame,
            text="⏹ Stop",
            font=('Arial', 12, 'bold'),
            bg='#e74c3c',
            fg='white',
            activebackground='#c0392b',
            activeforeground='white',
            cursor='hand2',
            height=2,
            command=self.stop_system,
            state=tk.DISABLED
        )
        self.btn_stop.pack(fill=tk.X, padx=15, pady=5)
        
        # Separator
        separator = ttk.Separator(right_frame, orient='horizontal')
        separator.pack(fill=tk.X, padx=15, pady=15)
        
        # Activity Log
        log_label = tk.Label(right_frame, text="Activity Log", font=('Arial', 12, 'bold'),
                            bg='#34495e', fg='white')
        log_label.pack(pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            right_frame,
            height=8,
            bg='#1a1a1a',
            fg='#00ff00',
            font=('Courier', 9),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, padx=15, pady=(5, 10))
        
        # IN/OUT Monitor Section
        monitor_label = tk.Label(right_frame, text="IN/OUT Monitor", font=('Arial', 12, 'bold'),
                                bg='#34495e', fg='white')
        monitor_label.pack(pady=5)
        
        # Monitor container with scrollbar
        monitor_container = tk.Frame(right_frame, bg='#34495e')
        monitor_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 10))
        
        # Canvas for scrolling
        self.monitor_canvas = tk.Canvas(monitor_container, bg='#ecf0f1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(monitor_container, orient="vertical", command=self.monitor_canvas.yview)
        self.monitor_frame = tk.Frame(self.monitor_canvas, bg='#ecf0f1')
        
        self.monitor_frame.bind(
            "<Configure>",
            lambda e: self.monitor_canvas.configure(scrollregion=self.monitor_canvas.bbox("all"))
        )
        
        self.monitor_canvas.create_window((0, 0), window=self.monitor_frame, anchor="nw")
        self.monitor_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.monitor_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initial message
        no_users_label = tk.Label(
            self.monitor_frame,
            text="No users yet",
            font=('Arial', 10),
            bg='#ecf0f1',
            fg='#999999'
        )
        no_users_label.pack(pady=20)
        
        # Statistics
        stats_frame = tk.Frame(right_frame, bg='#34495e')
        stats_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.stats_label = tk.Label(
            stats_frame,
            text="👥 Enrolled Users: 0 | ⏱ FPS: 0",
            font=('Arial', 9),
            bg='#34495e',
            fg='#ecf0f1'
        )
        self.stats_label.pack()
        
        # Initial log message
        self.log("System initialized and ready")
        self.update_stats()
        
        # Start periodic monitor update
        self.update_monitor()
    
    def log(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
    
    def update_status(self, message, color='#2ecc71'):
        """Update status bar"""
        self.status_label.config(text=message, bg=color)
    
    def update_stats(self):
        """Update statistics display"""
        enrolled = len(self.recognizer.known_names) if hasattr(self.recognizer, 'known_names') else 0
        self.stats_label.config(text=f"👥 Enrolled Users: {enrolled} | ⏱ FPS: 0")
    
    def update_monitor(self):
        """Update IN/OUT monitor display"""
        try:
            # Clear current display
            for widget in self.monitor_frame.winfo_children():
                widget.destroy()
            
            # Get enrolled users
            enrolled_names = []
            if hasattr(self.recognizer, 'known_names') and self.recognizer.known_names:
                enrolled_names = self.recognizer.known_names
            elif hasattr(self.recognizer, 'known_face_names') and self.recognizer.known_face_names:
                enrolled_names = self.recognizer.known_face_names
            else:
                # Fallback: read from images directory
                if os.path.exists(config.IMAGES_DIR):
                    enrolled_names = [d for d in os.listdir(config.IMAGES_DIR) 
                                    if os.path.isdir(os.path.join(config.IMAGES_DIR, d))]
            
            if not enrolled_names:
                no_users_label = tk.Label(
                    self.monitor_frame,
                    text="No users yet",
                    font=('Arial', 10),
                    bg='#ecf0f1',
                    fg='#999999'
                )
                no_users_label.pack(pady=20)
            else:
                # Get user status
                user_status = self.tracker.get_user_status()
                
                for name in enrolled_names:
                    status = user_status.get(name, {'status': 'OUT', 'last_time': 'N/A', 'duration': 'N/A'})
                    
                    # User card frame
                    card = tk.Frame(self.monitor_frame, bg='white', relief=tk.RAISED, borderwidth=1)
                    card.pack(fill=tk.X, padx=5, pady=5)
                    
                    # Left side - info
                    left_side = tk.Frame(card, bg='white')
                    left_side.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=8)
                    
                    # Name
                    name_label = tk.Label(
                        left_side,
                        text=name,
                        font=('Arial', 11, 'bold'),
                        bg='white',
                        fg='#333333',
                        anchor='w'
                    )
                    name_label.pack(anchor='w')
                    
                    # Time info
                    if status['status'] == 'IN':
                        time_info = f"In at: {status.get('check_in_time', status['last_time'])}"
                    elif status.get('check_out_time'):
                        time_info = f"In: {status.get('check_in_time', 'N/A')} → Out: {status['check_out_time']}"
                        if status.get('duration'):
                            time_info += f" • Total: {status['duration']}"
                    else:
                        time_info = "Not checked in today"
                    
                    info_label = tk.Label(
                        left_side,
                        text=time_info,
                        font=('Arial', 9),
                        bg='white',
                        fg='#666666',
                        anchor='w'
                    )
                    info_label.pack(anchor='w')
                    
                    # Right side - status and delete
                    right_side = tk.Frame(card, bg='white')
                    right_side.pack(side=tk.RIGHT, padx=10, pady=8)
                    
                    # Status badge
                    badge_color = '#2ecc71' if status['status'] == 'IN' else '#95a5a6'
                    status_badge = tk.Label(
                        right_side,
                        text=status['status'],
                        font=('Arial', 9, 'bold'),
                        bg=badge_color,
                        fg='white',
                        padx=10,
                        pady=3
                    )
                    status_badge.pack(side=tk.LEFT, padx=5)
                    
                    # Delete button
                    delete_btn = tk.Button(
                        right_side,
                        text="🗑 Delete",
                        font=('Arial', 9, 'bold'),
                        bg='#e74c3c',
                        fg='white',
                        activebackground='#c0392b',
                        cursor='hand2',
                        command=lambda n=name: self.delete_user(n)
                    )
                    delete_btn.pack(side=tk.LEFT, padx=5)
        
        except Exception as e:
            print(f"Error updating monitor: {e}")
        
        # Schedule next update
        self.root.after(2000, self.update_monitor)
    
    def delete_user(self, name):
        """Delete a user"""
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete {name}?\n\nThis will remove all their face data and cannot be undone."):
            try:
                import shutil
                
                # Remove user directory
                user_dir = os.path.join(config.IMAGES_DIR, name)
                if os.path.exists(user_dir):
                    shutil.rmtree(user_dir)
                    self.log(f"Deleted user directory: {name}")
                
                # Retrain recognizer
                self.recognizer.train()
                self.update_stats()
                self.log(f"✓ Removed user: {name}")
                messagebox.showinfo("Success", f"{name} deleted successfully!")
                
            except Exception as e:
                self.log(f"ERROR deleting user: {str(e)}")
                messagebox.showerror("Error", f"Failed to delete {name}: {str(e)}")
    
    def toggle_mode(self, mode):
        """Start the system in specified mode"""
        if self.running:
            self.log(f"Already running in {self.current_mode} mode")
            return
        
        self.current_mode = mode
        self.running = True
        
        # Update button states
        self.btn_attendance.config(state=tk.DISABLED)
        self.btn_access.config(state=tk.DISABLED)
        self.btn_enroll.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        
        mode_name = "Attendance" if mode == 'attendance' else "Access Control"
        self.log(f"Starting {mode_name} mode...")
        self.update_status(f"Running: {mode_name} Mode", '#3498db')
        
        # Start camera thread
        self.camera_thread = threading.Thread(target=self.run_recognition, daemon=True)
        self.camera_thread.start()
    
    def stop_system(self):
        """Stop the recognition system"""
        self.running = False
        self.log("Stopping system...")
        
        # Wait for thread to finish
        if self.camera_thread:
            self.camera_thread.join(timeout=2.0)
        
        # Release camera
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Clear video display
        self.video_label.config(image='')
        
        # Update button states
        self.btn_attendance.config(state=tk.NORMAL)
        self.btn_access.config(state=tk.NORMAL)
        self.btn_enroll.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        
        self.log("System stopped")
        self.update_status("Ready", '#2ecc71')
        self.current_mode = None
    
    def run_recognition(self):
        """Main recognition loop"""
        try:
            # Initialize camera
            self.camera = Camera()
            self.log("Camera initialized")
            
            frame_count = 0
            fps_start_time = time.time()
            fps = 0
            last_recognition = {}
            
            while self.running:
                frame = self.camera.read_frame()
                if frame is None:
                    self.log("Failed to read frame from camera")
                    time.sleep(0.1)
                    continue
                
                frame_count += 1
                
                # Calculate FPS
                if frame_count % 30 == 0:
                    fps = 30 / (time.time() - fps_start_time)
                    fps_start_time = time.time()
                    enrolled = len(self.recognizer.known_names) if hasattr(self.recognizer, 'known_names') else 0
                    self.stats_label.config(text=f"👥 Enrolled Users: {enrolled} | ⏱ FPS: {fps:.1f}")
                
                # Process every Nth frame
                if frame_count % config.PROCESS_EVERY_N_FRAMES == 0:
                    # Detect faces
                    face_locations = self.detector.detect_faces(frame)
                    
                    if len(face_locations) > 0:
                        # Recognize faces
                        face_names = self.recognizer.recognize_faces(frame, face_locations)
                        
                        # Process each recognized face
                        for (x, y, w, h), name in zip(face_locations, face_names):
                            if name != "Unknown":
                                current_time = time.time()
                                
                                # Check cooldown
                                if name not in last_recognition or \
                                   current_time - last_recognition[name] > 3.0:
                                    
                                    last_recognition[name] = current_time
                                    
                                    if self.current_mode == 'attendance':
                                        status = self.tracker.check_in_out(name)
                                        self.log(f"✓ {name}: {status}")
                                    else:  # access mode
                                        self.log(f"✓ Access GRANTED: {name}")
                            
                            # Draw rectangle and name
                            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                            cv2.putText(frame, name, (x, y - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # Display frame
                self.display_frame(frame)
                
                # Small delay
                time.sleep(0.01)
                
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.update_status(f"Error: {str(e)}", '#e74c3c')
        finally:
            if self.camera:
                self.camera.release()
    
    def display_frame(self, frame):
        """Display frame in GUI"""
        try:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize to fit display
            display_height = 480
            aspect_ratio = frame.shape[1] / frame.shape[0]
            display_width = int(display_height * aspect_ratio)
            frame_resized = cv2.resize(frame_rgb, (display_width, display_height))
            
            # Convert to PhotoImage
            img = Image.fromarray(frame_resized)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update label
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            
        except Exception as e:
            pass  # Ignore display errors
    
    def enroll_face(self):
        """Open enrollment dialog"""
        EnrollDialog(self.root, self)
    
    def on_closing(self):
        """Handle window closing"""
        if self.running:
            self.stop_system()
        self.root.destroy()


class EnrollDialog:
    """Dialog for enrolling new faces"""
    
    def __init__(self, parent, app):
        self.app = app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Enroll New Face")
        self.dialog.geometry("500x450")
        self.dialog.configure(bg='#34495e')
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.camera = None
        self.running = False
        self.captured_images = []
        self.detector = FaceDetector()
        self.is_capturing = False
        self.capture_delay = 0
        self.user_name = ""
        
        self.setup_ui()
        self.start_preview()
    
    def setup_ui(self):
        """Setup enrollment dialog UI"""
        # Instructions
        instructions = tk.Label(
            self.dialog,
            text="Look at the camera. System will auto-capture 3 images.",
            font=('Arial', 11, 'bold'),
            bg='#34495e',
            fg='white'
        )
        instructions.pack(pady=10)
        
        # Name entry
        name_frame = tk.Frame(self.dialog, bg='#34495e')
        name_frame.pack(pady=10)
        
        tk.Label(name_frame, text="Name:", font=('Arial', 11), bg='#34495e', fg='white').pack(side=tk.LEFT, padx=5)
        self.name_entry = tk.Entry(name_frame, font=('Arial', 11), width=25)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        
        # Start button
        self.btn_start = tk.Button(
            name_frame,
            text="▶ Start",
            font=('Arial', 10, 'bold'),
            bg='#27ae60',
            fg='white',
            command=self.start_auto_capture
        )
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        # Preview
        self.preview_label = tk.Label(self.dialog, bg='black')
        self.preview_label.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Progress
        self.progress_label = tk.Label(
            self.dialog,
            text="Enter name and click Start",
            font=('Arial', 10, 'bold'),
            bg='#34495e',
            fg='#ecf0f1'
        )
        self.progress_label.pack(pady=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.dialog,
            length=400,
            mode='determinate',
            maximum=3
        )
        self.progress_bar.pack(pady=5)
        
        # Status
        self.status_label = tk.Label(
            self.dialog,
            text="Ready",
            font=('Arial', 9),
            bg='#2ecc71',
            fg='white',
            height=2
        )
        self.status_label.pack(fill=tk.X, padx=20, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.dialog, bg='#34495e')
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="✗ Cancel",
            font=('Arial', 11, 'bold'),
            bg='#e74c3c',
            fg='white',
            width=15,
            command=self.cancel
        ).pack(side=tk.LEFT, padx=5)
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def auto_save_and_train(self):
        """Automatically save and train after capturing images"""
        try:
            self.progress_label.config(text="Auto-saving and training...", fg='#3498db')
            self.status_label.config(text="Saving images...", bg='#3498db')
            
            # Create user directory
            user_dir = os.path.join(config.IMAGES_DIR, self.user_name)
            os.makedirs(user_dir, exist_ok=True)
            
            # Save images
            for idx, img in enumerate(self.captured_images):
                filename = f"{self.user_name}_{idx+1}.jpg"
                filepath = os.path.join(user_dir, filename)
                cv2.imwrite(filepath, img)
            
            self.status_label.config(text="Training model...", bg='#9b59b6')
            
            # Retrain recognizer
            self.app.recognizer.train()
            self.app.update_stats()
            self.app.log(f"✓ Enrolled new user: {self.user_name} ({len(self.captured_images)} images)")
            
            self.status_label.config(text="✓ Success!", bg='#2ecc71')
            self.progress_label.config(text=f"✓ {self.user_name} enrolled successfully!", fg='#2ecc71')
            
            # Show success notification
            messagebox.showinfo("Success!", f"✓ {self.user_name} enrolled successfully!\n\n{len(self.captured_images)} face samples captured and trained.")
            
            # Close dialog
            self.cancel()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
            self.status_label.config(text="Error occurred", bg='#e74c3c')
    
    def start_preview(self):
        """Start camera preview"""
        self.running = True
        self.camera = Camera()
        threading.Thread(target=self.preview_loop, daemon=True).start()
    
    def start_auto_capture(self):
        """Start automatic face capture"""
        self.user_name = self.name_entry.get().strip()
        
        if not self.user_name:
            messagebox.showwarning("Warning", "Please enter a name first")
            return
        
        if self.is_capturing:
            return
        
        self.is_capturing = True
        self.captured_images = []
        self.progress_bar['value'] = 0
        self.name_entry.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.DISABLED)
        self.progress_label.config(text="Look at the camera...", fg='#f39c12')
        self.status_label.config(text="Detecting face...", bg='#f39c12')
    
    def preview_loop(self):
        """Preview camera feed and auto-capture"""
        frame_count = 0
        
        while self.running:
            frame = self.camera.read_frame()
            if frame is None:
                time.sleep(0.03)
                continue
            
            display_frame = frame.copy()
            
            # Auto-capture logic
            if self.is_capturing and len(self.captured_images) < 3:
                frame_count += 1
                
                # Detect face every 3 frames
                if frame_count % 3 == 0:
                    face_locations = self.detector.detect_faces(frame)
                    
                    if len(face_locations) > 0:
                        # Found a face
                        self.status_label.config(text="Face detected! Capturing...", bg='#27ae60')
                        
                        # Draw rectangle on detected face
                        for (x, y, w, h) in face_locations:
                            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                            cv2.putText(display_frame, "Capturing...", (x, y - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        # Capture with delay (faster - every 5 frames)
                        self.capture_delay += 1
                        if self.capture_delay >= 5:
                            self.captured_images.append(frame.copy())
                            count = len(self.captured_images)
                            self.progress_bar['value'] = count
                            self.progress_label.config(text=f"Captured: {count}/3")
                            self.capture_delay = 0
                            
                            # Auto-save and train when done
                            if count >= 3:
                                self.is_capturing = False
                                self.auto_save_and_train()
                    else:
                        # No face detected
                        self.status_label.config(text="No face detected - please face the camera", bg='#e67e22')
                        cv2.putText(display_frame, "No face detected", (50, 50),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                        self.capture_delay = 0
            
            # Display frame
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (400, 300))
            img = Image.fromarray(frame_resized)
            imgtk = ImageTk.PhotoImage(image=img)
            self.preview_label.imgtk = imgtk
            self.preview_label.configure(image=imgtk)
            
            time.sleep(0.03)
    
    def capture_image(self):
        """Capture current frame"""
        if len(self.captured_images) >= 20:
            messagebox.showinfo("Complete", "Already captured 20 images")
            return
        
        frame = self.camera.read_frame()
        if frame is not None:
            self.captured_images.append(frame.copy())
            self.progress_label.config(text=f"Images captured: {len(self.captured_images)}/20")
            
            if len(self.captured_images) >= 20:
                self.btn_capture.config(state=tk.DISABLED)
    
    def save_and_train(self):
        """Save images and train recognizer"""
        name = self.user_name if self.user_name else self.name_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Warning", "Please enter a name")
            return
        
        if len(self.captured_images) < 3:
            messagebox.showwarning("Warning", f"Only {len(self.captured_images)} images captured. Need at least 3.")
            return
        
        try:
            self.status_label.config(text="Saving images...", bg='#3498db')
            
            # Create user directory
            user_dir = os.path.join(config.IMAGES_DIR, name)
            os.makedirs(user_dir, exist_ok=True)
            
            # Save images
            for idx, img in enumerate(self.captured_images):
                filename = f"{name}_{idx+1}.jpg"
                filepath = os.path.join(user_dir, filename)
                cv2.imwrite(filepath, img)
            
            self.status_label.config(text="Training model...", bg='#9b59b6')
            
            # Retrain recognizer
            self.app.recognizer.train()
            self.app.update_stats()
            self.app.log(f"✓ Enrolled new user: {name} ({len(self.captured_images)} images)")
            
            messagebox.showinfo("Success", f"Successfully enrolled {name}!\n{len(self.captured_images)} images saved.")
            self.cancel()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
            self.status_label.config(text="Error occurred", bg='#e74c3c')
    
    def cancel(self):
        """Cancel and close dialog"""
        self.running = False
        if self.camera:
            self.camera.release()
        self.dialog.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = FaceRecognitionApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
