# 🌍 국내 여행 추천 프로그램

사용자가 입력한 날짜를 기반으로 AI가 국내 여행지를 추천하고, 지도 API로 맛집을 검색한 후, 최종 여행 리포트를 생성하는 프로그램입니다.

## 프로그램 개요

이 프로그램은 다음 3가지 주요 기능을 수행합니다:

1. **LLM 기반 여행지 추천** (OpenAI API)
   - 입력된 날짜에 맞는 국내 여행지 추천
   - 해당 시기의 날씨 정보 및 행사/축제 정보 제공

2. **맛집 검색** (NAVER 지도 API)
   - 추천 지역의 맛집 5곳 검색
   - 업체명, 주소, 카테고리, 방문 URL, 지도 좌표 제공

3. **여행 리포트 생성** (OpenAI API)
   - 추천 지역, 날씨, 행사, 맛집 정보 통합
   - Markdown 형식의 체계적인 여행 일정 제안

## 실행 환경

- **Python**: 3.10 이상 (현재: 3.12.13)
- **OS**: macOS, Linux, Windows
- **필수 패키지**: `openai`, `requests`, `python-dotenv`

## 설정 및 실행 방법

### 1️⃣ 의존성 설치

가상환경을 활성화한 후 패키지를 설치합니다:

```bash
# 가상환경 생성 (이미 생성되어 있으면 건너뜀)
python3 -m venv .venv

# 가상환경 활성화 (macOS/Linux)
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2️⃣ API 키 설정

이 프로그램은 두 가지 API를 사용합니다:

#### OpenAI API Key
- 홈페이지: https://platform.openai.com/account/api-keys
- 가입 후 API 키 생성
- 활성화 및 결제 정보 필수

#### NAVER API HUB (Local Search API)
- 홈페이지: https://www.ncloud.com/product/apiService/apigw
- NAVER Cloud Platform 계정 필요
- **중요**: 구형 NAVER Developers API가 아니라 **NAVER API HUB**를 사용해야 합니다.
- Local Search API 활성화 필요
- Client ID (API Key ID)와 Client Secret (API Key) 발급

#### 환경변수 설정

`.env` 파일이 없으면 `.env.example`을 참고하여 `.env` 파일을 생성하세요:

```bash
# macOS/Linux 터미널에서
export OPENAI_API_KEY="your_openai_key_here"
export NAVER_API_KEY_ID="your_naver_client_id_here"
export NAVER_API_KEY="your_naver_client_secret_here"
```

또는 프로젝트 폴더에 `.env` 파일을 생성합니다:

```env
OPENAI_API_KEY=your_openai_key_here
NAVER_API_KEY_ID=your_naver_client_id_here
NAVER_API_KEY=your_naver_client_secret_here
```

### 3️⃣ 프로그램 실행

```bash
# 기본 실행
python travel_planner.py -date "2026-03-15"

# 다른 날짜로 실행
python travel_planner.py -date "2026-05-20"
```

**날짜 형식**: `YYYY-MM-DD` (예: 2026-03-15)

### 4️⃣ 실행 결과 확인

프로그램 실행 후 `results/` 폴더에 2개의 파일이 생성됩니다:

- **JSON 데이터 파일** (`2026-03-15_*.json`)
  - 1차 추천 결과 (지역, 날씨, 행사, 추천 이유)
  - 맛집 검색 결과 (5곳)
  - 오류 요약

- **Markdown 리포트** (`2026-03-15_*.md`)
  - 추천 지역 및 이유
  - 날씨 요약
  - 행사/축제 정보
  - 맛집 리스트
  - 1일 일정 제안

## 실행 예시

```bash
$ python travel_planner.py -date "2026-03-15"

🌍 여행 추천 프로그램 시작 (날짜: 2026-03-15)
============================================================

[1/3] 1차 추천 생성 중(LLM)...
  → 1차 추천 생성 중...
  ✓ 추천 지역: 제주

[2/3] 맛집 검색 중(지도/장소 API)...
  → 맛집 검색 중 (제주)...
  ✓ 맛집 5곳 검색 완료

[3/3] 최종 리포트 생성 중(LLM)...
  → 최종 리포트 생성 중...
  ✓ 리포트 생성 완료

결과 저장 중...
  ✓ 데이터: results/2026-03-15_20250911_120345_data.json
  ✓ 리포트: results/2026-03-15_20250911_120345_report.md

============================================================
✅ 완료!
📁 results/ 폴더에서 결과를 확인하세요.
```

## 보안 주의사항 ⚠️

### API 키 노출 방지

1. **코드에 직접 작성 금지**: API 키를 `travel_planner.py`에 하드코딩하지 마세요
2. **.env 파일 보호**: 
   - `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 자동으로 무시됩니다
   - 절대 GitHub 등에 업로드하면 안 됩니다
3. **환경변수 사용**: 프로덕션 환경에서는 시스템 환경변수를 사용하세요
4. **협업시 주의**: 팀원과 협업할 때는 `.env.example`를 공유하고, `.env`는 각자 로컬에서만 유지하세요

### 키 유출 시 대처

API 키가 실수로 공개되었다면:
1. 해당 API 서비스에서 키를 즉시 재발급하세요
2. 요금 청구 여부 확인
3. 클라우드 제공자 대시보드에서 접근 로그 확인

## 에러 처리

### API 키 미설정
```
❌ 오류: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.
   README.md의 '설정 및 실행 방법'을 참고하여 설정하세요.
```
→ **해결**: 위의 "API 키 설정" 섹션을 참고하여 환경변수 설정

### NAVER API 인증 실패 (HTTP 401/403)
```
⚠️  HTTP 401: 인증 실패(401). API 키 설정을 확인하세요.
```
→ **해결**: 
- `NAVER_API_KEY_ID`, `NAVER_API_KEY` 값 확인
- API HUB에서 Local Search API 활성화 확인
- 헤더명이 `X-NCP-APIGW-API-KEY-ID`/`X-NCP-APIGW-API-KEY`인지 확인

### 맛집 검색 결과 0건
```
⚠️  검색 결과 0건 (query=...)
```
→ **정상 동작**: 검색 결과가 없어도 리포트는 계속 생성되며, 맛집 섹션에 "데이터 없음" 표기

### LLM JSON 파싱 실패
```
⚠️  JSON 파싱 실패. 재시도 중...
```
→ **자동 처리**: 프롬프트를 단순화하여 자동으로 1회 재시도합니다

## 기술 상세

### 상용 API 사용
- **OpenAI API** (gpt-4o-mini): 여행지 추천, 최종 리포트 생성
- **NAVER Local Search API**: 맛집 정보 검색

### 주요 구현 내용
- REST API 요청/응답 처리 (`requests` 라이브러리)
- JSON 파싱 및 에러 핸들링
- 환경변수 보안 관리 (`python-dotenv`)
- CLI 인터페이스 구현 (`argparse`)
- 날짜 형식 검증

### 결과 파일 구조
```
results/
├── 2026-03-15_20250911_120345_data.json     # 원본 데이터
└── 2026-03-15_20250911_120345_report.md    # Markdown 리포트
```

## 파일 구조

```
travel_planner/
├── .env                    # API 키 (Git 무시)
├── .env.example            # 환경변수 템플릿
├── .gitignore              # Git 제외 파일 목록
├── .venv/                  # Python 가상환경
├── travel_planner.py       # 메인 프로그램
├── requirements.txt        # Python 의존성
├── README.md               # 이 파일
└── results/                # 실행 결과 저장 폴더
    └── 2026-03-15_*.json   # 각 실행의 결과 JSON
    └── 2026-03-15_*.md    # 각 실행의 결과 Markdown
```

## 학습 포인트

이 프로젝트를 완성하면 다음을 이해할 수 있습니다:

✅ REST API의 요청/응답 구조 및 HTTP 메서드 (GET/POST)  
✅ LLM API를 활용한 구조화된 출력 처리 (JSON → 다음 단계 입력)  
✅ 외부 API 호출 시 발생하는 대표 오류 및 대응 방법  
✅ API 키를 안전하게 관리하는 방법 (환경변수/`.env`)  
✅ 여러 API를 조합하여 통합된 서비스 구현  
✅ 프로덕션급 에러 처리 및 로깅  

## 라이센스

학습용 프로젝트입니다.

## 문의/버그 리포트

문제가 발생하면 터미널 출력 메시지를 확인하고, 위의 "에러 처리" 섹션을 참고하세요.

---

**마지막 업데이트**: 2026년 9월 11일
