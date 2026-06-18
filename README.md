# OpenFHE CKKS 기반 개인정보 보호 얼굴인증 시스템

본 프로젝트는 얼굴 특징벡터를 평문으로 서버에 노출하지 않고, CKKS 동형암호를 이용해 암호화된 상태에서 코사인 유사도를 계산하는 **1:1 얼굴인증 시스템**입니다.

## 주요 기능

* InsightFace `buffalo_l` 기반 512차원 얼굴 임베딩 추출
* 등록 이미지 5장의 평균 템플릿 생성 및 L2 정규화
* OpenFHE CKKS 기반 특징벡터 암호화
* 서버에서 `EvalMult`, `EvalSum`을 이용한 암호문 유사도 계산
* Flask 서버 및 SQLite 기반 암호화 템플릿 관리
* Plaintext와 CKKS 결과 비교
* FAR, FRR 및 Adaptive Threshold 측정

## 동작 과정

### 등록

1. 얼굴 이미지 5장에서 특징벡터 추출
2. 각 특징벡터 L2 정규화
3. 평균 템플릿 생성 후 재정규화
4. CKKS 암호화
5. 암호화된 템플릿만 서버에 저장

### 인증

1. 인증 이미지에서 특징벡터 추출
2. L2 정규화 후 CKKS 암호화
3. 서버에서 암호문 간 곱셈 및 합산 수행
4. 클라이언트에서 결과 복호화
5. Threshold와 비교하여 인증 성공 여부 결정

L2 정규화된 특징벡터는 코사인 유사도를 내적으로 계산할 수 있습니다.

```text
cosine_similarity(x, y) = x · y
```

## Adaptive Threshold

여러 임계값에 대해 FAR과 FRR을 계산한 뒤, 두 오류율 차이의 절댓값인 `|FAR - FRR|`이 최소가 되는 지점의 임계값을 Adaptive Threshold로 선택했습니다.

## 주요 실험 결과

| 항목                 |              결과 |
| ------------------ | --------------: |
| Adaptive Threshold |        0.546644 |
| FAR                |               0 |
| FRR                |               0 |
| Plaintext-CKKS 오차  | 약 10⁻¹⁴ ~ 10⁻¹² |
| 평균 CKKS 처리시간       |       47.799 ms |
| Binary 암호문 크기      |   787,679 Bytes |
| Base64 암호문 크기      | 1,050,240 Bytes |

## 실행 방법

가상환경을 생성하고 필요한 패키지를 설치합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

의존성을 설치합니다.

```bash
pip install -r requirements.txt
```

## 로컬 이미지 준비

얼굴 이미지는 개인정보 보호를 위해 GitHub 저장소에 포함하지 않습니다.

실행 전 로컬 환경에 다음과 같이 등록 이미지를 준비합니다.

```text
client/
└── register/
    └── user123/
        ├── me1.jpg
        ├── me2.jpg
        ├── me3.jpg
        ├── me4.jpg
        └── me5.jpg
```

인증 요청 이미지는 프로젝트 코드에서 지정한 `verify` 경로에 준비합니다.

```text
client/
└── verify/
    └── query.jpg
```

현재 `user_id`는 `user123`으로 하드코딩되어 있으며, 이 부분은 추후 수정할 예정입니다.

## 서버 실행

```bash
cd server
python3 server.py
```

## 클라이언트 실행

새 터미널에서 프로젝트 가상환경을 활성화한 뒤 실행합니다.

```bash
source .venv/bin/activate
cd client
python3 ckks_client.py
```

## 보안 주의사항

다음 파일과 디렉터리는 저장소에 포함하지 않습니다.

```text
*.jpg
*.jpeg
*.key
*.db
*.sqlite
.env
venv/
.venv/
register/
verify/
keys/
```

본 프로젝트는 제한된 데이터셋과 단일 요청 환경에서 개인정보 보호형 얼굴인증 시스템의 적용 가능성을 확인하는 것을 목적으로 합니다.
