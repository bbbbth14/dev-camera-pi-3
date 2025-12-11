"""
Face Recognition Module
Handles face encoding and recognition using face_recognition library
"""

import face_recognition
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional
import config


class FaceRecognizer:
    """Face recognizer using face_recognition library"""
    
    def __init__(self):
        """Initialize the face recognizer"""
        self.known_face_encodings = []
        self.known_face_names = []
        self.encodings_file = os.path.join(config.FACES_DIR, 'encodings.pkl')
        
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
        # Convert BGR to RGB
        rgb_image = image[:, :, ::-1]
        
        # Detect face locations
        face_locations = face_recognition.face_locations(rgb_image, model=config.MODEL)
        
        if len(face_locations) == 0:
            print("[WARNING] No face detected in image")
            return None
        
        if len(face_locations) > 1:
            print("[WARNING] Multiple faces detected, using the first one")
        
        # Generate encoding for the first detected face
        encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        if len(encodings) > 0:
            return encodings[0]
        
        return None
    
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
        
        # Convert BGR to RGB
        rgb_image = image[:, :, ::-1]
        
        # Detect face locations and encodings
        face_locations = face_recognition.face_locations(rgb_image, model=config.MODEL)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        
        results = []
        
        for face_encoding in face_encodings:
            # Compare with known faces
            matches = face_recognition.compare_faces(
                self.known_face_encodings,
                face_encoding,
                tolerance=config.RECOGNITION_TOLERANCE
            )
            
            # Calculate face distances
            face_distances = face_recognition.face_distance(
                self.known_face_encodings,
                face_encoding
            )
            
            name = "Unknown"
            confidence = 0.0
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    # Convert distance to confidence (0-1, where 1 is perfect match)
                    confidence = 1 - face_distances[best_match_index]
            
            results.append((name, confidence))
        
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
