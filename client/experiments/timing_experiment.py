import os
import time
import glob
import numpy as np

from config import *
from embedding import *
from print_utils import *
from crypto_utils import *
from api_utils import *


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