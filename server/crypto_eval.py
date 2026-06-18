from openfhe import *
import base64
import time
import hashlib

param = CCParamsCKKSRNS()
param.SetBatchSize(1024)

cc = GenCryptoContext(param)
cc.Enable(PKESchemeFeature.PKE)
cc.Enable(PKESchemeFeature.LEVELEDSHE)
cc.Enable(PKESchemeFeature.ADVANCEDSHE)

eval_keys_loaded = False

def load_eval_keys_once(eval_mult_key_b64, eval_sum_key_b64):
    global eval_keys_loaded

    if eval_keys_loaded:
        return

    eval_mult_bytes = base64.b64decode(eval_mult_key_b64.encode("utf-8"))
    eval_sum_bytes = base64.b64decode(eval_sum_key_b64.encode("utf-8"))

    DeserializeEvalMultKeyString(eval_mult_bytes, BINARY)
    DeserializeEvalAutomorphismKeyString(eval_sum_bytes, BINARY)

    eval_keys_loaded = True
    print("eval keys loaded")


def short_sha256(data: bytes) -> str:
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()[:16]  # 앞 16자리만 반환

def compute_encrypted_similarity(encrypted_template, encrypted_query, eval_mult_key_b64, eval_sum_key_b64):
    load_eval_keys_once(eval_mult_key_b64, eval_sum_key_b64)

    template_bytes = base64.b64decode(
        encrypted_template.encode("utf-8")
    )
    query_bytes = base64.b64decode(
        encrypted_query.encode("utf-8")
    )

    template_cipher = DeserializeCiphertextString(
        template_bytes, BINARY
    )
    query_cipher = DeserializeCiphertextString(
        query_bytes, BINARY
    )

    print("\n================ SERVER CKKS TRACE ================")
    print("[1] DB에서 불러온 Template")
    print("Template binary size :", len(template_bytes), "bytes")
    print("Template SHA-256     :", short_sha256(template_bytes))
    print("Template object type :", type(template_cipher).__name__)

    print("\n[2] Client에서 받은 Query")
    print("Query binary size    :", len(query_bytes), "bytes")
    print("Query SHA-256        :", short_sha256(query_bytes))
    print("Query object type    :", type(query_cipher).__name__)

    start = time.perf_counter()

    multiply_cipher = cc.EvalMult(
        template_cipher,
        query_cipher
    )
    similarity_cipher = cc.EvalSum(
        multiply_cipher,
        512
    )

    end = time.perf_counter()
    ckks_time = end - start

    sim_bytes = Serialize(similarity_cipher, BINARY)
    sim_b64 = base64.b64encode(sim_bytes).decode("utf-8")

    print("\n[3] 서버 동형암호 연산")
    print("Operation 1          : EvalMult(template, query)")
    print("Operation 2          : EvalSum(multiply, 512)")
    print("Result binary size   :", len(sim_bytes), "bytes")
    print("Result SHA-256       :", short_sha256(sim_bytes))
    print("Result object type   :", type(similarity_cipher).__name__)



    return sim_b64, ckks_time
