import os
import glob
import time
import numpy as np
import base64

from config import *
from embedding import *
from print_utils import *
from crypto_utils import *
from api_utils import *

TEMPLATE_COUNT = 5

def register_user(public_key):
    register_dir = os.path.join(BASE_DIR, "images", "register", USER_ID)
    image_paths = sorted(glob.glob(os.path.join(register_dir, "*.jpg")))

    if len(image_paths) == 0:
        print("등록할 이미지가 없습니다:", register_dir)
        return

    image_paths = image_paths[:TEMPLATE_COUNT]

    avg_embedding = make_average_embedding(image_paths)
    avg_cipher = encrypt_embedding(avg_embedding, public_key)
    avg_cipher_b64 = serialize_cipher(avg_cipher)

    plain_embedding_size = avg_embedding.nbytes
    ciphertext_binary_size = len(base64.b64decode(avg_cipher_b64))
    ciphertext_base64_size = len(avg_cipher_b64)

    print("\n[데이터 크기]")
    print("Plain embedding size:", plain_embedding_size, "bytes")
    print("Ciphertext binary size:", ciphertext_binary_size, "bytes")
    print("Ciphertext Base64 size:", ciphertext_base64_size, "bytes")

    response = register_request(USER_ID, KEY_ID, avg_cipher_b64)

    print_register_result(
        USER_ID,
        KEY_ID,
        image_paths,
        avg_embedding,
        response,
        avg_cipher_b64
    )

def verify_one(public_key, secret_key):
    verify_user_id = input("비교할 등록 user id 입력: ")

    query_image_name = input("인증 요청 이미지 파일명 입력: ")
    query_image_path = os.path.join(BASE_DIR, "images", "verify", query_image_name)

    print("query image path:", query_image_path)

    query_embedding = extract_embedding(query_image_path)

    query_cipher = encrypt_embedding(query_embedding, public_key)
    query_cipher_b64 = serialize_cipher(query_cipher)

    #plaintext similarity계산
    register_dir = os.path.join(BASE_DIR, "images", "register", verify_user_id)
    registered_image_paths = sorted(glob.glob(os.path.join(register_dir, "*.jpg")))

    if len(registered_image_paths) == 0:
        print("등록된 이미지가 없습니다:", register_dir)
        return

    registered_image_paths = registered_image_paths[:TEMPLATE_COUNT]

    client_reg_avg_emb = make_average_embedding(registered_image_paths)
    start = time.time()
    plaintext_similarity = float(
        np.dot(client_reg_avg_emb, query_embedding)
    )
    end = time.time()
    plaintext_time = end-start
    response = verify_request(verify_user_id, KEY_ID, query_cipher_b64)

    if response.status_code != 200:
        print("verify failed:", response.status_code, response.text)
        return

    result = response.json()
    ckks_time = result["time"]
    similarity_cipher_b64 = result["encrypted_similarity"]
    similarity_cipher = deserialize_cipher(similarity_cipher_b64)
    ckks_similarity = decrypt_cipher(similarity_cipher, secret_key)[0]

    print_verify_result(
        verify_user_id,
        KEY_ID,
        query_image_name,
        query_embedding,
        query_cipher_b64,
        similarity_cipher_b64,
        ckks_similarity,
        plaintext_similarity,
        plaintext_time,
        ckks_time
    )


def run_verify_experiment(public_key, secret_key):
    verify_user_id = USER_ID

    verify_dir = os.path.join(BASE_DIR, "images", "verify")
    verify_image_paths = sorted(glob.glob(os.path.join(verify_dir, "*.jpg")))

    if len(verify_image_paths) == 0:
        print("verify 이미지가 없습니다:", verify_dir)
        return

    register_dir = os.path.join(BASE_DIR, "images", "register", verify_user_id)
    registered_image_paths = sorted(glob.glob(os.path.join(register_dir, "*.jpg")))

    if len(registered_image_paths) == 0:
        print("등록된 이미지가 없습니다:", register_dir)
        return

    registered_avg_embedding = make_average_embedding(registered_image_paths[:TEMPLATE_COUNT])

    results = []

    print(f"\n================== {verify_user_id}와 전체 비교  ===================")
    print(f"DB에 저장된 {verify_user_id}의 평균 embedding 값과 verify 폴더 이미지를 비교")

    for image_path in verify_image_paths:
        image_name = os.path.basename(image_path)

        query_embedding = extract_embedding(image_path)

        plaintext_similarity = float(np.dot(registered_avg_embedding, query_embedding))

        query_cipher = encrypt_embedding(query_embedding, public_key)
        query_cipher_b64 = serialize_cipher(query_cipher)

        response = verify_request(verify_user_id, KEY_ID, query_cipher_b64)

        if response.status_code != 200:
            print(image_name, "verify 실패:", response.status_code, response.text)
            continue

        result = response.json()

        similarity_cipher_b64 = result["encrypted_similarity"]
        similarity_cipher = deserialize_cipher(similarity_cipher_b64)

        ckks_similarity = float(decrypt_cipher(similarity_cipher, secret_key)[0])
        error = abs(ckks_similarity - plaintext_similarity)

        results.append({
            "image": image_name,
            "plaintext": plaintext_similarity,
            "ckks": ckks_similarity,
            "error": error
        })

    results.sort(key=lambda x: x["ckks"], reverse=True)

    print_verify_all_result(results)
    
    
def genuine_impostor():
    register_dir = os.path.join(BASE_DIR, "images", "register", USER_ID)
    verify_dir = os.path.join(BASE_DIR, "images", "verify")

    registered_image_paths = sorted(glob.glob(os.path.join(register_dir, "*.jpg")))[:TEMPLATE_COUNT]
    registered_avg_embedding = make_average_embedding(registered_image_paths)

    verify_image_paths = sorted(glob.glob(os.path.join(verify_dir, "*.jpg")))

    genuine_scores = []
    impostor_scores = []
    for image_path in verify_image_paths:
        image_name = os.path.basename(image_path)

        query_embedding = extract_embedding(image_path)
        score = float(np.dot(registered_avg_embedding, query_embedding))

        if image_name.startswith("me"):
            genuine_scores.append(score)
        else:
            impostor_scores.append(score)
        
    return genuine_scores, impostor_scores

        
def calc_adaptivethreshold():
    genuine, impostor = genuine_impostor()
    genuine = np.array(genuine)
    impostor = np.array(impostor)
    
    all_scores = np.sort(np.concatenate([genuine, impostor]))
    
    best_threshold = None
    best_far = None
    best_frr = None
    best_diff = float("inf")
    
    for threshold in all_scores:
        far = np.mean(impostor >= threshold)
        frr = np.mean(genuine < threshold)
        
        diff = abs(far-frr)
        
        if diff < best_diff:
            best_diff = diff
            best_threshold = threshold
            best_far = far
            best_frr = frr
    return best_threshold, best_far, best_frr

def run_distribution_experiment():
    print("\nTemplate Count:", TEMPLATE_COUNT)
    genuine_scores, impostor_scores = genuine_impostor()
    threshold, far, frr = calc_adaptivethreshold()
    print_distribution_experiment_result(genuine_scores, impostor_scores)
    
    print("\n[Adaptive Threshold]")
    print("threshold:", threshold)
    print("FAR:", far)
    print("FRR:", frr)
    print("EER:", (far + frr) / 2)
    thresholds = [0.40, 0.45, 0.50, 0.55, 0.60]

    for th in thresholds:
        far = sum(s >= th for s in impostor_scores) / len(impostor_scores)
        frr = sum(s < th for s in genuine_scores) / len(genuine_scores)

        print("Temporary Threshold:", th, "FAR:", far, "FRR:", frr)
        
def run_timing_experiment(public_key, secret_key):
    verify_user_id = USER_ID

    query_image_name = input(
        "시간 측정에 사용할 인증 이미지 파일명 입력: "
    )

    query_image_path = os.path.join(
        BASE_DIR,
        "images",
        "verify",
        query_image_name
    )

    if not os.path.exists(query_image_path):
        print("이미지가 존재하지 않습니다:", query_image_path)
        return

    # 얼굴 특징 추출 시간은 측정 대상에서 제외한다.
    query_embedding = extract_embedding(query_image_path)

    # 평문 비교용 등록 평균 embedding 생성
    register_dir = os.path.join(
        BASE_DIR,
        "images",
        "register",
        verify_user_id
    )

    registered_image_paths = sorted(
        glob.glob(os.path.join(register_dir, "*.jpg"))
    )

    if len(registered_image_paths) < TEMPLATE_COUNT:
        print(
            f"등록 이미지가 부족합니다. "
            f"필요: {TEMPLATE_COUNT}, 현재: {len(registered_image_paths)}"
        )
        return

    registered_image_paths = registered_image_paths[:TEMPLATE_COUNT]

    registered_avg_embedding = make_average_embedding(
        registered_image_paths
    )

    warmup_count = 3
    repeat_count = 30

    plaintext_times = []
    encrypt_times = []
    eval_times = []
    decrypt_times = []
    total_ckks_times = []

    print("\n================ 연산 시간 반복 측정 ================")
    print("Template Count:", TEMPLATE_COUNT)
    print("Query Image:", query_image_name)
    print("Warm-up Count:", warmup_count)
    print("Measurement Count:", repeat_count)
    print("=====================================================\n")

    total_repeat = warmup_count + repeat_count

    for i in range(total_repeat):

        # -------------------------------------------------
        # 1. Plaintext cosine similarity 시간
        # -------------------------------------------------
        # np.dot 한 번은 너무 빨라서 시간 오차가 클 수 있으므로
        # 1000번 실행한 뒤 평균 시간을 계산한다.
        plaintext_repeat = 1000

        plaintext_start = time.perf_counter()

        for _ in range(plaintext_repeat):
            plaintext_similarity = float(
                np.dot(
                    registered_avg_embedding,
                    query_embedding
                )
            )

        plaintext_end = time.perf_counter()

        plaintext_time = (
            plaintext_end - plaintext_start
        ) / plaintext_repeat

        # -------------------------------------------------
        # 2. CKKS Encrypt 시간
        # -------------------------------------------------
        encrypt_start = time.perf_counter()

        query_cipher = encrypt_embedding(
            query_embedding,
            public_key
        )

        encrypt_end = time.perf_counter()

        encrypt_time = encrypt_end - encrypt_start

        # 직렬화 시간은 Encrypt 시간에서 제외
        query_cipher_b64 = serialize_cipher(query_cipher)

        # -------------------------------------------------
        # 3. 서버 EvalMult + EvalSum
        # -------------------------------------------------
        response = verify_request(
            verify_user_id,
            KEY_ID,
            query_cipher_b64
        )

        if response.status_code != 200:
            print(
                "verify 실패:",
                response.status_code,
                response.text
            )
            return

        result = response.json()

        eval_time = float(result["time"])

        similarity_cipher_b64 = result["encrypted_similarity"]

        # 역직렬화 시간은 Decrypt 시간에서 제외
        similarity_cipher = deserialize_cipher(
            similarity_cipher_b64
        )

        # -------------------------------------------------
        # 4. CKKS Decrypt 시간
        # -------------------------------------------------
        decrypt_start = time.perf_counter()

        ckks_similarity = float(
            decrypt_cipher(
                similarity_cipher,
                secret_key
            )[0]
        )

        decrypt_end = time.perf_counter()

        decrypt_time = decrypt_end - decrypt_start

        total_ckks_time = (
            encrypt_time
            + eval_time
            + decrypt_time
        )

        # 최초 3회는 OpenFHE 준비 및 캐시 영향을 줄이기 위한
        # 워밍업이므로 결과에 포함하지 않는다.
        if i >= warmup_count:
            plaintext_times.append(plaintext_time)
            encrypt_times.append(encrypt_time)
            eval_times.append(eval_time)
            decrypt_times.append(decrypt_time)
            total_ckks_times.append(total_ckks_time)

        current_number = i + 1

        if i < warmup_count:
            print(
                f"Warm-up {current_number}/{warmup_count} 완료"
            )
        else:
            measurement_number = i - warmup_count + 1

            print(
                f"Measurement "
                f"{measurement_number}/{repeat_count} 완료"
            )

    def print_time_statistics(title, values):
        values = np.array(values, dtype=np.float64)

        print(f"\n[{title}]")
        print(f"평균      : {np.mean(values):.9f} sec")
        print(f"표준편차  : {np.std(values, ddof=1):.9f} sec")
        print(f"최소      : {np.min(values):.9f} sec")
        print(f"최대      : {np.max(values):.9f} sec")

    print("\n\n================ 시간 측정 최종 결과 ================")

    print_time_statistics(
        "Plaintext Similarity",
        plaintext_times
    )

    print_time_statistics(
        "CKKS Encrypt",
        encrypt_times
    )

    print_time_statistics(
        "EvalMult + EvalSum",
        eval_times
    )

    print_time_statistics(
        "CKKS Decrypt",
        decrypt_times
    )

    print_time_statistics(
        "Total CKKS",
        total_ckks_times
    )

    print("\n[마지막 연산 결과 확인]")
    print("Plaintext Similarity:", plaintext_similarity)
    print("CKKS Similarity:", ckks_similarity)
    print(
        "Absolute Error:",
        abs(plaintext_similarity - ckks_similarity)
    )

    print("=====================================================\n")

    

    