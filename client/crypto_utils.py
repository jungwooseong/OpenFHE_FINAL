import os
import base64
import numpy as np
from openfhe import *

from config import KEY_DIR, PUBLIC_KEY_PATH, SECRET_KEY_PATH, BATCH_SIZE

os.makedirs(KEY_DIR, exist_ok=True)

def create_context():
    param = CCParamsCKKSRNS()
    param.SetBatchSize(BATCH_SIZE)

    cc = GenCryptoContext(param)
    cc.Enable(PKESchemeFeature.PKE)
    cc.Enable(PKESchemeFeature.LEVELEDSHE)
    cc.Enable(PKESchemeFeature.ADVANCEDSHE)

    return cc

cc = create_context()


def load_or_create_keys():
    if os.path.exists(PUBLIC_KEY_PATH) and os.path.exists(SECRET_KEY_PATH):
        with open(PUBLIC_KEY_PATH, "rb") as f:
            public_key = DeserializePublicKeyString(f.read(), BINARY)

        with open(SECRET_KEY_PATH, "rb") as f:
            secret_key = DeserializePrivateKeyString(f.read(), BINARY)

        return public_key, secret_key

    key_pair = cc.KeyGen()

    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(Serialize(key_pair.publicKey, BINARY))

    with open(SECRET_KEY_PATH, "wb") as f:
        f.write(Serialize(key_pair.secretKey, BINARY))

    return key_pair.publicKey, key_pair.secretKey

def b64_encode(data):
    return base64.b64encode(data).decode("utf-8")

def b64_decode(data):
    return base64.b64decode(data.encode("utf-8"))

def serialize_cipher(cipher):
    return b64_encode(Serialize(cipher, BINARY))

def deserialize_cipher(cipher_b64):
    return DeserializeCiphertextString(b64_decode(cipher_b64), BINARY)

def generate_eval_keys(secret_key):
    cc.EvalMultKeyGen(secret_key)
    cc.EvalSumKeyGen(secret_key)

    return (
        b64_encode(SerializeEvalMultKeyString(BINARY)),
        b64_encode(SerializeEvalAutomorphismKeyString(BINARY))
    )

def encrypt_embedding(embedding, public_key):
    plaintext = cc.MakeCKKSPackedPlaintext(embedding)
    return cc.Encrypt(public_key, plaintext)

def decrypt_cipher(cipher, secret_key):
    decrypted = cc.Decrypt(cipher, secret_key)
    values = decrypted.GetCKKSPackedValue()

    return np.array([v.real for v in values], dtype=np.float64)

