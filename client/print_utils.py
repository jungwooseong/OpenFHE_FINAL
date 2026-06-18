import os
import numpy as np
from config import THRESHOLD


def short_vector(vector, count=5):
    return [round(float(v), 6) for v in vector[:count]]

def line(title):
    print("\n=======================", title, "========================")

def print_register_result(user_id, key_id, image_paths, avg_embedding, response, avg_cipher_b64=None):
    line("등록 과정")

    print("[1] 등록 사용자 정보")
    print("user_id:", user_id)
    print("key_id:", key_id)

    print("\n[2] 사용한 얼굴 이미지")
    print("이미지 개수:", len(image_paths))
    for image_path in image_paths:
        print("-", os.path.basename(image_path))

    print("\n[3] 평균 embedding 생성")
    print("embedding 차원:", len(avg_embedding))
    print("embedding 앞부분:", short_vector(avg_embedding))

    print("\n[4] CKKS 암호화")
    if avg_cipher_b64 is not None:
        print("암호문 크기:", len(avg_cipher_b64))
        print("암호문 일부:", "..."+avg_cipher_b64[-120:])

    print("\n[5] 서버 저장 결과")
    print("status:", response.status_code)
    print("response:", response.text)

    print("\n설명: 서버에는 원본 이미지나 평문 embedding이 아니라 encrypt된 avg embedding만 저장된다.")
    print("============================================================\n")

def print_verify_result(
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
    
):
    line("인증 과정")

    print("[1] 비교 대상")
    print("DB에 저장된 사용자:", verify_user_id)
    print("key_id:", KEY_ID)
    print("인증 요청 이미지:", query_image_name)

    print("\n[2] 인증 이미지 embedding")
    print("embedding 차원:", len(query_embedding))
    print("embedding 앞부분:", short_vector(query_embedding))

    print("\n[3] 인증 embedding 암호화")
    print("query 암호문 크기:", len(query_cipher_b64))
    print("query 암호문 일부:", "..." + query_cipher_b64[-120:])

    print("\n[4] 서버에서 수행한 CKKS 연산")
    print("EvalMult(template_cipher, query_cipher)")
    print("EvalSum(..., 512)")


    print("\n[5] 서버가 반환한 encrypted similarity")
    print("encrypted similarity 크기:", len(similarity_cipher_b64))
    print("encrypted similarity 일부:", "..."+similarity_cipher_b64[-120:])

    print("\n[6] 클라이언트 복호화 결과")
    print("CKKS cosine similarity:", ckks_similarity)

    if plaintext_similarity is not None:
        print("\n[7] 평문 계산값과 비교")
        print("평문 cosine similarity:", plaintext_similarity)
        print("CKKS cosine similarity:", ckks_similarity)
        print("절대 오차:", f"{abs(ckks_similarity - plaintext_similarity):.15f}")

    
    print("임시 threshold:", THRESHOLD)
    
    print("\n[8] Plaintext calc time vs CKKS calc time")
    print(f"Plaintext Similarity time : {plaintext_time :.9f}sec")
    print(f"CKKS Similarity time : {ckks_time:.9f}sec")
    print()

    if ckks_similarity >= THRESHOLD:
        print("인증 결과: 성공")
    else:
        print("인증 결과: 실패")
    print("============================================================\n")


def print_verify_all_result(results):
    print("\n========================= 결과 요약 =========================")
    print("image\t\tplaintext\tckks\t\tabsolute error\t\tresult")
    print("--------------------------------------------------------------")

    for item in results:
        print(
            f"{item['image']:<12}\t"
            f"{item['plaintext']:.6f}\t"
            f"{item['ckks']:.6f}\t"
            f"{item['error']:.15f}\t" , end =""
        )
        if(item['ckks'] >= THRESHOLD):
            print("PASS")
        else:
            print("FAIL")

    print("\n설명:")
    print("plaintext는 클라이언트에서 평문 embedding으로 직접 계산한 cosine similarity")
    print("ckks는 서버에서 암호문끼리 EvalMult + EvalSum을 수행한 뒤 클라이언트가 복호화한 값")
    print("두 similarity의 차를 통해 오차 계산")
    print("=============================================================\n")
    
def print_distribution_experiment_result(genuine_scores, impostor_scores):
    print("\n================== Genuine / Impostor 분포 ==================")

    print("\n[Genuine - 본인 이미지]")
    print("개수:", len(genuine_scores))
    print("평균:", np.mean(genuine_scores))
    print("표준편차:", np.std(genuine_scores))
    print("최소:", np.min(genuine_scores))
    print("최대:", np.max(genuine_scores))

    print("\n[Impostor - 타인 이미지]")
    print("개수:", len(impostor_scores))
    print("평균:", np.mean(impostor_scores))
    print("표준편차:", np.std(impostor_scores))
    print("최소:", np.min(impostor_scores))
    print("최대:", np.max(impostor_scores))

    separation_gap = np.min(genuine_scores) - np.max(impostor_scores)

    print("\n[분포 간격]")
    print("Separation Gap:", separation_gap)

    print("\n[참고]")
    print("Genuine은 user123 본인 이미지와 비교한 점수")
    print("Impostor는 verify에 존재하는 타인 이미지와 비교한 점수")
    print("=============================================================\n")