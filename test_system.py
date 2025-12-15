#!/usr/bin/env python3
"""
Test script to verify the face recognition system without camera
"""

import cv2
import numpy as np
from face_detector import FaceDetector
from face_recognizer import FaceRecognizer

print("=" * 50)
print("Testing Face Recognition System")
print("=" * 50)

# Test 1: Face Detector
print("\n[TEST 1] Testing Face Detector...")
try:
    detector = FaceDetector()
    print("✓ Face Detector initialized successfully")
except Exception as e:
    print(f"✗ Face Detector failed: {e}")
    exit(1)

# Test 2: Face Recognizer
print("\n[TEST 2] Testing Face Recognizer...")
try:
    recognizer = FaceRecognizer()
    print("✓ Face Recognizer initialized successfully")
    print(f"  Known faces: {len(recognizer.known_face_names)}")
except Exception as e:
    print(f"✗ Face Recognizer failed: {e}")
    exit(1)

# Test 3: Create dummy image and test detection
print("\n[TEST 3] Testing face detection on dummy image...")
try:
    # Create a simple grayscale test image
    test_image = np.ones((480, 640, 3), dtype=np.uint8) * 200
    faces = detector.detect_faces(test_image)
    print(f"✓ Face detection works (found {len(faces)} face(s) in test image)")
except Exception as e:
    print(f"✗ Face detection failed: {e}")
    exit(1)

# Test 4: Test OpenCV modules
print("\n[TEST 4] Testing OpenCV modules...")
try:
    print(f"  OpenCV version: {cv2.__version__}")
    print(f"  cv2.face module: {'Available' if hasattr(cv2, 'face') else 'Not Available'}")
    if hasattr(cv2, 'face'):
        print("✓ OpenCV face module is available")
    else:
        print("✗ OpenCV face module not found")
        exit(1)
except Exception as e:
    print(f"✗ OpenCV check failed: {e}")
    exit(1)

print("\n" + "=" * 50)
print("All tests passed! ✓")
print("=" * 50)
print("\nThe system is ready to use.")
print("Run './start.sh' to start the face recognition system.")
