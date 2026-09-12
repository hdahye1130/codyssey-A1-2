# 국내 여행 추천 프로그램

입력한 날짜에 맞는 국내 여행지를 **Google Gemini 2.5 Flash**로 추천하고, **NAVER API HUB Local Search**에서 맛집을 검색한 뒤 Markdown 여행 리포트를 만듭니다. OpenAI API는 사용하지 않습니다.

## 준비

Python 3.10 이상을 준비하고 프로젝트 폴더에서 가상환경을 만듭니다.

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
pip install -r requirements.txt
```

Windows에서는 가상환경 활성화 명령으로 `.venv\Scripts\activate`(명령 프롬프트) 또는 `.venv\Scripts\Activate.ps1`(PowerShell)을 사용하세요. `requirements.txt`에는 Gemini용 `google-genai`, NAVER HTTP 요청용 `requests`, `.env` 로드용 `python-dotenv`가 포함되어 있습니다.

Google Gemini API 키와 NAVER API HUB Local Search용 API Key ID 및 API Key를 발급받으세요. 프로젝트 폴더에서 `.env.example`을 복사해 `.env`를 만든 뒤, 아래 세 값에 **본인의 키**를 입력합니다.

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
NAVER_API_KEY_ID=YOUR_NAVER_API_HUB_CLIENT_ID
NAVER_API_KEY=YOUR_NAVER_API_HUB_CLIENT_SECRET
```

macOS/Linux에서는 `.env` 대신 같은 이름의 환경변수를 셸에 `export`해도 됩니다. 프로그램은 `python-dotenv`의 `load_dotenv()`로 `.env`를 읽습니다. NAVER Developers의 기존 Local Search가 아닌 **NAVER API HUB Local Search** 키가 필요합니다.

**API 키를 소스코드나 README에 적거나 GitHub에 올리지 마세요.** 실제 키가 들어간 `.env`는 로컬에만 두세요. 이 프로젝트의 `.gitignore`는 `.env`를 제외하지만, 커밋 전 변경 파일을 확인하는 것이 안전합니다.

## 실행과 결과 확인

가상환경을 활성화한 상태에서 날짜를 `YYYY-MM-DD` 형식으로 입력합니다.

```bash
python travel_planner.py -date "YYYY-MM-DD"
```

예: `python travel_planner.py -date "2026-11-30"`

실행 후 터미널에 표시되는 경로 또는 `results/` 폴더에서 결과를 확인하세요. 파일 이름에는 여행 날짜와 실행 시각이 들어갑니다.

- `*_data.json`: 추천 지역, 날씨, 행사, 추천 이유, 맛집 정보와 `errors` 배열
- `*_report.md`: 추천 내용과 맛집을 종합한 Markdown 리포트

추천이 성공하면 맛집을 최대 5곳 검색합니다. NAVER의 `mapx`는 경도(`x`), `mapy`는 위도(`y`)로 저장하며, 1e7 스케일로 반환된 좌표는 실제 소수 좌표로 변환합니다. API 오류가 발생해도 가능한 결과는 JSON에 저장하고 오류는 `errors`에 기록합니다. **Markdown 파일은 최종 리포트 생성에 성공했을 때만 생성됩니다.**

## API가 동작하는 방식

REST API는 프로그램이 서버에 요청을 보내고 응답을 받는 방식입니다. **GET**은 주로 데이터를 조회할 때, **POST**는 데이터를 서버에 보내 처리해 달라고 할 때 사용합니다. 이 프로그램은 Gemini SDK로 날짜를 보내 추천을 받고, NAVER API HUB Local Search에 **GET** 요청으로 `추천 지역 + 맛집`을 검색합니다. 이어서 Gemini SDK에 추천과 맛집을 전달해 최종 Markdown 리포트를 받습니다. Gemini 호출의 HTTP 처리는 SDK가 담당하므로 이 코드에서 직접 GET/POST를 작성하지 않습니다.

첫 추천의 JSON 파싱에 실패하면 더 간단한 프롬프트로 한 번 재요청합니다. 최종 리포트 생성 중 Gemini가 503, UNAVAILABLE 또는 high demand 오류를 반환하면 잠시 기다린 뒤 **한 번만** 재시도합니다. 재시도 후에도 실패하면 `errors`에 기록하고 프로그램은 결과 저장을 계속합니다.
