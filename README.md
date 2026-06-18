# OpenFHE CKKS 기반 개인정보 보호 얼굴인증 시스템

본 프로젝트는 얼굴 특징벡터를 평문으로 서버에 노출하지 않고, **CKKS 동형암호를 이용해 암호화된 상태에서 코사인 유사도를 계산하는 1:1 얼굴인증 시스템**입니다.

## 주요 기능

* InsightFace `buffalo_l` 기반 512차원 얼굴 임베딩 추출
* 등록 이미지 5장의 평균 템플릿 생성 및 L2 정규화
* OpenFHE CKKS 기반 특징벡터 암호화
* `EvalMult`, `EvalSum`을 이용한 암호문 유사도 계산
* Flask 서버 및 SQLite 기반 암호화 템플릿 관리
* Plaintext와 CKKS 계산 결과 비교
* FAR, FRR 및 Adaptive Threshold 측정

## 동작 과정

### 등록

1. 얼굴 이미지 5장에서 특징벡터를 추출합니다.
2. 각 특징벡터를 L2 정규화합니다.
3. 평균 템플릿을 생성한 후 다시 정규화합니다.
4. 평균 템플릿을 CKKS로 암호화합니다.
5. 암호화된 템플릿만 서버에 저장합니다.

### 인증

1. 인증 이미지에서 특징벡터를 추출합니다.
2. 특징벡터를 L2 정규화한 후 CKKS로 암호화합니다.
3. 서버에서 등록 템플릿과 Query 암호문을 곱하고 합산합니다.
4. 클라이언트에서 유사도 결과를 복호화합니다.
5. Threshold와 비교하여 인증 성공 여부를 결정합니다.

L2 정규화된 특징벡터는 코사인 유사도를 내적으로 계산할 수 있습니다.

```text
cosine_similarity(x, y) = x · y
```

## Adaptive Threshold

여러 임계값에 대해 FAR과 FRR을 계산한 뒤, 두 오류율 차이의 절댓값인 `|FAR - FRR|`이 최소가 되는 지점의 임계값을 Adaptive Threshold로 선택합니다.

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

## 프로젝트 구조

```text
OpenFHE_FINAL/
├── client/
│   ├── experiments/
│   ├── api_utils.py
│   ├── ckks_client.py
│   ├── config.py
│   ├── crypto_utils.py
│   ├── embedding.py
│   ├── print_utils.py
│   └── service.py
│
├── server/
│   ├── app.py
│   ├── crypto_eval.py
│   └── db.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

## 설치 방법

저장소를 내려받습니다.

```bash
git clone https://github.com/jungwooseong/OpenFHE_FINAL.git
cd OpenFHE_FINAL
```

프로젝트 루트에 서버와 클라이언트가 함께 사용하는 가상환경을 하나 생성합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 로컬 이미지 준비

얼굴 이미지는 개인정보 보호를 위해 GitHub 저장소에 포함하지 않습니다.

등록 이미지는 다음 경로에 준비합니다.

```text
client/
└── images/
    └── register/
        └── user123/
            ├── me1.jpg
            ├── me2.jpg
            ├── me3.jpg
            ├── me4.jpg
            └── me5.jpg
```

인증 이미지는 다음 경로에 준비합니다.

```text
client/
└── images/
    └── verify/
        └── query.jpg
```

현재 기본 설정은 다음과 같습니다.

```text
USER_ID = user123
KEY_ID = global_key_v1
SERVER_URL = http://127.0.0.1:5000
```

설정은 `client/config.py`에서 변경할 수 있습니다.

## 실행 방법

프로젝트 루트에서 가상환경을 활성화합니다.

```bash
source .venv/bin/activate
```

### 서버 실행

첫 번째 터미널에서 실행합니다.

```bash
python3 server/app.py
```

서버는 기본적으로 `5000`번 포트에서 실행됩니다.

### 클라이언트 실행

두 번째 터미널에서 동일한 가상환경을 활성화한 후 실행합니다.

```bash
source .venv/bin/activate
python3 client/ckks_client.py
```

클라이언트 메뉴:

```text
r: 사용자 등록
v: 단일 인증
a: Plaintext와 CKKS 전체 비교
d: Genuine/Impostor 분포 실험
q: 종료
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
keys/
client/images/
```

실제 얼굴 이미지, 암호키, 데이터베이스 및 사용자 생체정보를 공개 저장소에 업로드하지 마십시오.

## 연구 범위

본 프로젝트는 제한된 데이터셋과 단일 요청 환경에서 개인정보 보호형 얼굴인증 시스템의 적용 가능성을 확인하는 것을 목적으로 합니다.
