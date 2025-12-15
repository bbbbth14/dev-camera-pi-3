"""
Face Recognition Module
Handles face encoding and recognition using OpenCV
"""

import cv2
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional
import config


class FaceRecognizer:
    """Face recognizer using OpenCV LBPH (Local Binary Patterns Histograms)"""
    
    def __init__(self):
        """Initialize the face recognizer"""
        self.known_face_encodings = []
        self.known_face_names = []
        self.encodings_file = os.path.join(config.FACES_DIR, 'encodings.pkl')
        
        # Initialize OpenCV face recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Load existing encodings if available
        self.load_encodings()
        
        print(f"[INFO] Face recognizer initialized with {len(self.known_face_names)} known face(s)")
    
    def load_encodings(self):
        """Load face encodings from file"""
        if os.path.exists(self.encodings_file):
            try:
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data['encodings']
                    self.known_face_names = data['names']
                
                # Retrain the recognizer with loaded data
                if len(self.known_face_encodings) > 0:
                    labels = list(range(len(self.known_face_names)))
                    self.recognizer.train(self.known_face_encodings, np.array(labels))
                
                print(f"[INFO] Loaded {len(self.known_face_names)} face encoding(s)")
            except Exception as e:
                print(f"[ERROR] Failed to load encodings: {e}")
                self.known_face_encodings = []
                self.known_face_names = []
    
    def save_encodings(self):
        """Save face encodings to file"""
        try:
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names
            }
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(data, f)
            print(f"[INFO] Saved {len(self.known_face_names)} face encoding(s)")
        except Exception as e:
            print(f"[ERROR] Failed to save encodings: {e}")
    
    def encode_face(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate face encoding from image
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Face encoding array or None if no face detected
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect face locations
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            print("[WARNING] No face detected in image")
            return None
        
        if len(faces) > 1:
            print("[WARNING] Multiple faces detected, using the first one")
        
        # Extract the first detected face
        (x, y, w, h) = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        
        # Resize to standard size for consistency
        face_roi = cv2.resize(face_roi, (200, 200))
        
        return face_roi
    
    def add_face(self, name: str, image: np.ndarray) -> bool:
        """
        Add a new face to the known faces database
        
        Args:
            name: Person's name
            image: Image containing the face
            
        Returns:
            True if successful, False otherwise
        """
        encoding = self.encode_face(image)
        
        if encoding is None:
            return False
        
        # Check if name already exists
        if name in self.known_face_names:
            print(f"[WARNING] {name} already exists. Updating encoding.")
            idx = self.known_face_names.index(name)
            self.known_face_encodings[idx] = encoding
        else:
            self.known_face_encodings.append(encoding)
            self.known_face_names.append(name)
        
        # Retrain the recognizer
        if len(self.known_face_encodings) > 0:
            labels = list(range(len(self.known_face_names)))
            self.recognizer.train(self.known_face_encodings, np.array(labels))
        
        self.save_encodings()
        print(f"[INFO] Added/updated face for {name}")
        return True
    
    def recognize_faces(self, image: np.ndarray) -> List[Tuple[str, float]]:
        """
        Recognize faces in an image
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            List of tuples (name, confidence) for each detected face
        """
        if len(self.known_face_encodings) == 0:
            return []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect face locations
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        results = []
        
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv2.resize(face_roi, (200, 200))
            
            # Predict the face
            label, confidence = self.recognizer.predict(face_roi)
            
            # LBPH confidence is inverse (lower is better)
            # Convert to 0-1 scale where 1 is best match
            # Typical LBPH confidence values range from 0-100+
            if confidence < 50:  # Good match threshold
                name = self.known_face_names[label]
                # Normalize confidence (inverted and scaled)
                confidence_score = max(0, 1 - (confidence / 100))
            else:
                name = "Unknown"
                confidence_score = 0.0
            
            results.append((name, confidence_score))
        
        return results
    
    def remove_face(self, name: str) -> bool:
        """
        Remove a face from the database
        
        Args:
            name: Person's name to remove
            
        Returns:
            True if successful, False otherwise
        """
        if name in self.known_face_names:
            idx = self.known_face_names.index(name)
            del self.known_face_encodings[idx]
            del self.known_face_names[idx]
            self.save_encodings()
            print(f"[INFO] Removed {name} from database")
            return True
        
        print(f"[WARNING] {name} not found in database")
        return False
    
    def list_known_faces(self) -> List[str]:
        """
        Get list of all known face names
        
        Returns:
            List of names
        """
        return self.known_face_names.copy()


if __name__ == "__main__":
    """Test the face recognizer"""
    print("[INFO] Testing face recognizer...")
    
    recognizer = FaceRecognizer()
    print(f"[INFO] Known faces: {recognizer.list_known_faces()}")
