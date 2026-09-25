import os
import cv2
import numpy as np
import base64
import logging
import requests
from typing import Tuple, Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Configurable threshold from environment
THRESHOLD_COSINE = float(os.getenv("FACE_MATCH_THRESHOLD", "0.45"))

# Directory for ONNX models if needed
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

YUNET_MODEL_PATH = os.path.join(MODELS_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_recognition_sface_2021dec.onnx")

YUNET_URL = "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"


class FaceRecognitionService:
    def __init__(self):
        self.yunet = None
        self.sface = None
        self.haar_cascade = None
        self._init_models()

    def _download_model_if_missing(self, path: str, url: str):
        if not os.path.exists(path) or os.path.getsize(path) < 100000:
            try:
                logger.info(f"Downloading model to {path} from {url}...")
                resp = requests.get(url, allow_redirects=True, timeout=60)
                if resp.status_code == 200 and len(resp.content) > 100000:
                    with open(path, 'wb') as f:
                        f.write(resp.content)
                    logger.info(f"Model saved successfully: {path} ({len(resp.content)} bytes)")
                else:
                    logger.warning(f"Download response invalid for {url}: status {resp.status_code}")
            except Exception as e:
                logger.warning(f"Could not download model from {url}: {e}")

    def _init_models(self):
        # Attempt to prepare YuNet & SFace models
        try:
            self._download_model_if_missing(YUNET_MODEL_PATH, YUNET_URL)
            self._download_model_if_missing(SFACE_MODEL_PATH, SFACE_URL)

            if os.path.exists(YUNET_MODEL_PATH) and os.path.exists(SFACE_MODEL_PATH):
                self.yunet = cv2.FaceDetectorYN.create(
                    model=YUNET_MODEL_PATH,
                    config="",
                    input_size=(320, 320),
                    score_threshold=0.6,
                    nms_threshold=0.3,
                    top_k=5000
                )
                self.sface = cv2.FaceRecognizerSF.create(
                    model=SFACE_MODEL_PATH,
                    config=""
                )
                logger.info("OpenCV YuNet + SFace successfully loaded.")
        except Exception as e:
            logger.warning(f"YuNet/SFace initialization note: {e}")

        # Cascade fallback if present
        try:
            if hasattr(cv2, 'CascadeClassifier') and hasattr(cv2, 'data') and hasattr(cv2.data, 'haarcascades'):
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.haar_cascade = cv2.CascadeClassifier(cascade_path)
                logger.info("OpenCV Haar Cascade loaded as fallback.")
        except Exception as e:
            logger.debug(f"Haar Cascade fallback note: {e}")

    @staticmethod
    def decode_base64_image(image_data: str) -> Optional[np.ndarray]:
        """Decode base64 data URI string into OpenCV BGR numpy array."""
        try:
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            logger.error(f"Error decoding base64 image: {e}")
            return None

    def detect_face_bbox(self, img: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect the primary face bounding box (x, y, w, h).
        Returns None if no face is detected.
        """
        if img is None:
            return None

        h, w, _ = img.shape

        # Try YuNet first if available
        if self.yunet is not None:
            try:
                self.yunet.setInputSize((w, h))
                _, faces = self.yunet.detect(img)
                if faces is not None and len(faces) > 0:
                    box = faces[0][:4].astype(int)
                    x, y, bw, bh = box[0], box[1], box[2], box[3]
                    return (max(0, x), max(0, y), min(w - x, bw), min(h - y, bh))
            except Exception as e:
                logger.debug(f"YuNet detect error: {e}")

        # Fallback to Haar Cascade
        if self.haar_cascade is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.haar_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
            )
            if len(faces) > 0:
                # Return the largest face
                largest = max(faces, key=lambda f: f[2] * f[3])
                return tuple(int(v) for v in largest)

        return None

    def extract_face_embedding(self, img: np.ndarray) -> Optional[List[float]]:
        """
        Detect face and extract 128-d normalized embedding vector.
        Returns None if no face found.
        """
        if img is None:
            return None

        h, w, _ = img.shape

        # Method 1: SFace with YuNet
        if self.yunet is not None and self.sface is not None:
            try:
                self.yunet.setInputSize((w, h))
                _, faces = self.yunet.detect(img)
                if faces is not None and len(faces) > 0:
                    aligned_face = self.sface.alignCrop(img, faces[0])
                    feature = self.sface.feature(aligned_face)
                    # Feature is 1x128 float32 array
                    norm_feat = feature.flatten().tolist()
                    return norm_feat
            except Exception as e:
                logger.warning(f"SFace embedding failed, falling back: {e}")

        # Method 2: Robust fallback using Haar detection + Normalized Spatial LBP/DCT/Grid features
        bbox = self.detect_face_bbox(img)
        if bbox is None:
            return None

        x, y, bw, bh = bbox
        face_roi = img[y:y+bh, x:x+bw]
        if face_roi.size == 0:
            return None

        # Standardize face patch
        face_roi = cv2.resize(face_roi, (112, 112))
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # 8x8 spatial grid mean & std features (8*8*2 = 128 dimensions)
        grid_h, grid_w = 14, 14
        features = []
        for r in range(8):
            for c in range(8):
                cell = gray[r*grid_h:(r+1)*grid_h, c*grid_w:(c+1)*grid_w]
                mean_val = float(np.mean(cell))
                std_val = float(np.std(cell))
                features.extend([mean_val, std_val])

        features = np.array(features, dtype=np.float32)
        norm = np.linalg.norm(features)
        if norm > 1e-6:
            features = features / norm
        return features.tolist()

    @staticmethod
    def calculate_cosine_distance(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine distance between two embedding vectors:
        Cosine Distance = 1.0 - Cosine Similarity
        Values range between 0.0 (identical) and 2.0 (opposite).
        """
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 < 1e-6 or norm2 < 1e-6:
            return 1.0
        similarity = np.dot(v1, v2) / (norm1 * norm2)
        return float(1.0 - similarity)

    def find_matching_student(
        self,
        query_embedding: List[float],
        students_dict: Dict[str, Any],
        threshold: Optional[float] = None
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]], float]:
        """
        Match query embedding against stored student embeddings.
        Returns: (matched_uid, student_data, best_distance)
        If no match within threshold, returns (None, None, best_distance).
        """
        if not query_embedding or not students_dict:
            return None, None, 1.0

        if threshold is None:
            threshold = THRESHOLD_COSINE

        best_uid = None
        best_student = None
        min_distance = float('inf')

        for uid, sdata in students_dict.items():
            if not isinstance(sdata, dict):
                continue

            stored_embedding = sdata.get('faceEmbedding')
            if not stored_embedding:
                continue

            # Check if student is active
            if sdata.get('status', 'aktif') != 'aktif':
                continue

            dist = self.calculate_cosine_distance(query_embedding, stored_embedding)
            if dist < min_distance:
                min_distance = dist
                if dist <= threshold:
                    best_uid = uid
                    best_student = sdata

        return best_uid, best_student, min_distance


# Singleton instance
face_service = FaceRecognitionService()
