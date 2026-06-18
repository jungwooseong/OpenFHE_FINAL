import requests
from config import SERVER_URL

def setup_eval_keys(user_id, key_id, eval_mult_key, eval_sum_key):
    data = {
        "user_id": user_id,
        "key_id": key_id,
        "eval_mult_key": eval_mult_key,
        "eval_sum_key": eval_sum_key
    }

    return requests.post(f"{SERVER_URL}/setup", json=data)

def register_request(user_id, key_id, encrypted_embedding_b64):
    data = {
        "user_id": user_id,
        "key_id": key_id,
        "encrypted_embedding": encrypted_embedding_b64
    }

    return requests.post(f"{SERVER_URL}/register", json=data)

def verify_request(user_id, key_id, query_cipher_b64):
    data = {
        "user_id": user_id,
        "key_id": key_id,
        "encrypted_embedding": query_cipher_b64
    }

    return requests.post(f"{SERVER_URL}/verify", json=data)

