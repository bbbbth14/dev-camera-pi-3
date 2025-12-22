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
        self.known_names = []  # Alias for compatibility
        self.encodings_file = os.path.join(config.FACES_DIR, 'encodings.pkl')
        
        # Initialize OpenCV face recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Load existing encodings if available
        self.load_encodings()
        
        print(f"[INFO] Face recognizer initialized with {len(self.known_face_names)} known face(s)")
    
    def load_encodings(self):
        """Load face encodings from file and retrain"""
        # Instead of loading pickled data, just retrain from images
        # This is more reliable
        if os.path.exists(config.IMAGES_DIR):
            user_dirs = [d for d in os.listdir(config.IMAGES_DIR) 
                        if os.path.isdir(os.path.join(config.IMAGES_DIR, d))]
            if len(user_dirs) > 0:
                print(f"[INFO] Found {len(user_dirs)} enrolled users, retraining...")
                self.train()
            else:
                print("[INFO] No enrolled users found")
        else:
            print(f"[WARNING] Images directory not found: {config.IMAGES_DIR}")
    
    def save_encodings(self):
        """Save face encodings to file"""
        try:
            # Build labels array: each encoding gets the index of its name
            labels = []
            for i, encoding in enumerate(self.known_face_encodings):
                # Find which user this encoding belongs to based on saved order
                # This is tricky, so let's not save/load trained model, just retrain
                pass
            
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names
            }
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(data, f)
            print(f"[INFO] Saved {len(self.known_face_encodings)} encodings for {len(self.known_face_names)} users")
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
    
    def recognize_faces(self, image: np.ndarray, face_locations: List[Tuple[int, int, int, int]] = None) -> List[str]:
        """
        Recognize faces in an image
        
        Args:
            image: Input image (BGR format)
            face_locations: Optional list of face locations (x, y, w, h)
            
        Returns:
            List of names for each detected face
        """
        if len(self.known_face_encodings) == 0:
            return []
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        results = []
        
        # If face locations provided, use them; otherwise detect faces
        if face_locations is not None and len(face_locations) > 0:
            # Use provided face locations (x, y, w, h format)
            for (x, y, w, h) in face_locations:
                
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (200, 200))
                
                # Predict the face
                label, confidence = self.recognizer.predict(face_roi)
                
                # LBPH confidence is inverse (lower is better)
                if confidence < 70:  # Good match threshold
                    name = self.known_face_names[label]
                else:
                    name = "Unknown"
                
                results.append(name)
        else:
            # Detect faces ourselves
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (200, 200))
                
                # Predict the face
                label, confidence = self.recognizer.predict(face_roi)
                
                # LBPH confidence is inverse (lower is better)
                if confidence < 70:  # Good match threshold
                    name = self.known_face_names[label]
                else:
                    name = "Unknown"
                
                results.append(name)
        
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
    
    def train(self):
        """
        Train the recognizer from all images in the images directory
        
        Returns:
            True if successful, False otherwise
        """
        print("[INFO] Training face recognizer from images...")
        
        self.known_face_encodings = []
        self.known_face_names = []
        
        if not os.path.exists(config.IMAGES_DIR):
            print(f"[ERROR] Images directory not found: {config.IMAGES_DIR}")
            return False
        
        # Get all user directories
        user_dirs = [d for d in os.listdir(config.IMAGES_DIR) 
                    if os.path.isdir(os.path.join(config.IMAGES_DIR, d))]
        
        if len(user_dirs) == 0:
            print("[WARNING] No user directories found")
            return False
        
        encodings = []
        labels = []
        names = []
        
        for user_name in user_dirs:
            user_path = os.path.join(config.IMAGES_DIR, user_name)
            image_files = [f for f in os.listdir(user_path) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            if len(image_files) == 0:
                print(f"[WARNING] No images found for {user_name}")
                continue
            
            print(f"[INFO] Processing {len(image_files)} images for {user_name}")
            
            # Add user to names list
            if user_name not in names:
                names.append(user_name)
            
            user_label = names.index(user_name)
            
            # Process each image
            for img_file in image_files:
                img_path = os.path.join(user_path, img_file)
                
                try:
                    # Read image
                    image = cv2.imread(img_path)
                    if image is None:
                        print(f"[WARNING] Failed to read {img_path}")
                        continue
                    
                    # Encode face
                    encoding = self.encode_face(image)
                    
                    if encoding is not None:
                        encodings.append(encoding)
                        labels.append(user_label)
                    
                except Exception as e:
                    print(f"[ERROR] Failed to process {img_path}: {e}")
        
        if len(encodings) == 0:
            print("[ERROR] No valid face encodings generated")
            return False
        
        # Update class variables
        self.known_face_encodings = encodings
        self.known_face_names = names
        self.known_names = names  # Sync alias
        
        # Train the LBPH recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.recognizer.train(encodings, np.array(labels))
        
        # Save encodings
        self.save_encodings()
        
        print(f"[SUCCESS] Training complete! {len(encodings)} encodings for {len(names)} users")
        print(f"[INFO] Enrolled users: {', '.join(names)}")
        
        return True


if __name__ == "__main__":
    """Test the face recognizer"""
    print("[INFO] Testing face recognizer...")
    
    recognizer = FaceRecognizer()
    print(f"[INFO] Known faces: {recognizer.list_known_faces()}")

