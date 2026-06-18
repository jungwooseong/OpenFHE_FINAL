import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_ID = "user123"
KEY_ID = "global_key_v1"

SERVER_URL = "http://127.0.0.1:5000"

KEY_DIR = os.path.join(BASE_DIR, "keys")
PUBLIC_KEY_PATH = os.path.join(KEY_DIR, "public.key")
SECRET_KEY_PATH = os.path.join(KEY_DIR, "secret.key")

THRESHOLD = 0.5466443664303687 - 0.0000001 # CKKS연산 시 소수점 오차를 감안하여 약간 낮춘 값.

BATCH_SIZE = 1024
EMBEDDING_DIM = 512
