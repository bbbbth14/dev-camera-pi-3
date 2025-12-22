"""
Camera Wrapper for Raspberry Pi
Supports both rpicam-still/rpicam-vid and USB cameras
"""

import cv2
import subprocess
import os
import time
import tempfile
import threading
from typing import Optional
import numpy as np


class Camera:
    """Universal camera wrapper with live preview support"""
    
    def __init__(self, width=640, height=480, use_pi_camera=True, preview=False):
        """
        Initialize camera
        
        Args:
            width: Frame width
            height: Frame height
            use_pi_camera: Try Pi Camera first
            preview: Enable live preview window
        """
        self.width = width
        self.height = height
        self.camera_type = None
        self.cap = None
        self.temp_file = os.path.join(tempfile.gettempdir(), 'picam_capture.jpg')
        self.preview = preview
        self.last_frame = None
        
        if use_pi_camera:
            # Try rpicam-still first
            if self._check_rpicam():
                self.camera_type = 'rpicam'
                print("[INFO] Using Pi Camera (rpicam-still)")
                return
        
        # Fallback to USB camera
        self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera_type = 'usb'
            print("[INFO] Using USB Camera")
        else:
            self.camera_type = None
            print("[ERROR] No camera available")
    
    def _check_rpicam(self) -> bool:
        """Check if rpicam-still is available"""
        try:
            result = subprocess.run(['which', 'rpicam-still'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def isOpened(self) -> bool:
        """Check if camera is available"""
        return self.camera_type is not None
    
    def read(self) -> tuple:
        """
        Capture a frame
        
        Returns:
            (success, frame) tuple
        """
        if self.camera_type == 'rpicam':
            success, frame = self._read_rpicam()
        elif self.camera_type == 'usb':
            success, frame = self.cap.read()
        else:
            return False, None
        
        # Store last frame for preview
        if success and frame is not None:
            self.last_frame = frame.copy()
        
        return success, frame
    
    def read_frame(self):
        """
        Convenience method to read a frame (returns frame only)
        
        Returns:
            frame or None if failed
        """
        success, frame = self.read()
        return frame if success else None
    
    def show_frame(self, frame, window_name="Camera Preview"):
        """
        Display frame in window if preview is enabled
        
        Args:
            frame: Frame to display
            window_name: Window title
        """
        if self.preview and frame is not None:
            cv2.imshow(window_name, frame)
            cv2.waitKey(1)
    
    def _read_rpicam(self) -> tuple:
        """Capture frame using rpicam-still"""
        try:
            # Capture image with rpicam-still
            cmd = [
                'rpicam-still',
                '-o', self.temp_file,
                '--width', str(self.width),
                '--height', str(self.height),
                '-t', '1',  # 1ms timeout (immediate)
                '--nopreview',
                '-n'  # No preview window
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            
            if result.returncode == 0 and os.path.exists(self.temp_file):
                # Read the captured image
                frame = cv2.imread(self.temp_file)
                if frame is not None:
                    return True, frame
            
            return False, None
            
        except Exception as e:
            print(f"[ERROR] rpicam capture failed: {e}")
            return False, None
    
    def release(self):
        """Release camera resources"""
        if self.camera_type == 'usb' and self.cap is not None:
            self.cap.release()
        
        # Clean up temp file
        if os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()


def test_camera():
    """Test camera capture"""
    print("[INFO] Testing camera...")
    
    with Camera() as cam:
        if not cam.isOpened():
            print("[ERROR] Failed to open camera")
            return False
        
        print(f"[INFO] Camera type: {cam.camera_type}")
        
        # Capture a test frame
        ret, frame = cam.read()
        
        if ret and frame is not None:
            print(f"[SUCCESS] Captured frame: {frame.shape}")
            
            # Save test image
            test_file = 'data/images/camera_test.jpg'
            os.makedirs('data/images', exist_ok=True)
            cv2.imwrite(test_file, frame)
            print(f"[INFO] Test image saved to {test_file}")
            return True
        else:
            print("[ERROR] Failed to capture frame")
            return False


if __name__ == "__main__":
    test_camera()
