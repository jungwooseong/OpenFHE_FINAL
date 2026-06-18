import os
import warnings

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
warnings.filterwarnings("ignore")

import cv2
import numpy as np
from insightface.app import FaceAnalysis

face_app = None


def init_face_detector():
    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )
    app.prepare(ctx_id=-1, det_size=(640, 640))

    return app


def extract_embedding(img_path):
    global face_app

    if face_app is None:
        face_app = init_face_detector()

    img = cv2.imread(img_path)

    if img is None:
        raise ValueError(f"Could not read image: {img_path}")

    faces = face_app.get(img)

    if len(faces) == 0:
        raise ValueError(f"No face detected: {img_path}")

    face = max(
        faces,
        key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
    )

    embedding = np.array(face.normed_embedding, dtype=np.float64)
    
    return embedding

def make_average_embedding(image_paths):
    if len(image_paths) == 0:
        raise ValueError("image_paths is empty")

    embeddings = []

    for image_path in image_paths:
        embedding = extract_embedding(image_path)
        embeddings.append(embedding)

    avg_embedding = np.mean(embeddings, axis=0)
    avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)

    return avg_embedding