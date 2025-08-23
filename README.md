## 들여다밭(Agrilook) 백엔드 API

팀: vigil

### 서비스 요약

- 비료 추천: POST `/api/fertilizer-recommendation` (밑거름/웃거름 각각 최대 3개)
  - 입력: `cropname`, `farmid` (본문 JSON)
  - 출력: 작물 정보(`crop`), 퇴비 추천(`compost`), 비료 추천(`fertilizer.base`, `fertilizer.additional`)

- 날씨 정보: GET `/api/weather/current?station=관측소번호`
  - 출력: `temperature`, `humidity`, `precipitation`, `weather`

- 챗봇(RAG): POST `/api/chat`
  - 입력: `message`
  - 출력: `answer`, `routing`, `sources`

- 토양 검사: GET `/api/soil/sensor`, `/api/soil/satellite`
  - 출력: 최신 토양 검사 결과

- 침입자 감지: GET `/api/intruder/recent`
  - 24시간 내 침입자 감지 데이터 + Azure Blob Storage 이미지
  - 출력: 감지 로그, 이미지 URL, 클래스별 카운트
  - 챗봇: 침입자 정보는 캐시를 통해 자동으로 프롬프트에 포함

농촌진흥청 비료·퇴비 처방 API와 기상 데이터를 활용해 작물별 비료·퇴비 추천을 제공하는 Flask 기반 백엔드입니다. 프론트엔드와의 계약은 JSON 스키마로 고정되어 있으며, 운영 환경에서는 표준 로깅을 사용합니다.

## 주요 기능

- 비료/퇴비 처방: 작물 코드와 토양·면적 정보를 바탕으로 밑거름/웃거름 추천
- 기상 조회: 관측소 기준 현재 기상 요약 제공
- 챗봇 RAG: 벡터 저장소 + BM25 앙상블 검색 기반 질의응답
- 토양 검사: 센서/위성 기반 최신 토양 데이터 조회
- 침입자 감지: MongoDB 로그 + Azure Blob Storage 이미지 연동

## 설치

1) 파이썬 환경 준비 (Python 3.10+ 권장)

2) 의존성 설치
```
pip install -r requirements.txt
```

3) 환경변수 설정
```
cp example.env .env
# .env 파일을 열어 키/설정을 채웁니다
```

4) 실행
```
python app.py
```
기본 포트는 5001입니다. `PORT` 또는 `FLASK_DEBUG` 등은 `.env`로 제어합니다.

## 환경변수(.env)

- FERTILIZER_API_KEY: 공공데이터포털 비료·퇴비 API 키 (필수)
- KMA_API_KEY: 기상청 API 키 (필수)
- OPENAI_API_KEY: 임베딩 생성용 OpenAI 키 (선택)
- MONGO_URI, DB_NAME: DB 사용 시 연결 정보
- AZURE_BLOB_BASE_URL: 침입자 이미지 Azure Blob Storage URL
- LOG_LEVEL: 기본 INFO (DEBUG 권장하지 않음, 민감정보 로그 금지)
- FLASK_DEBUG: "1"이면 디버그 모드
- PORT: 미설정 시 5001

## API

### 1) 비료·퇴비 추천
POST `/api/fertilizer-recommendation`

요청 예시
```json
{
  "cropname": "맥주보리",
  "farmid": "farm001"
}
```

응답 예시
```json
{
  "_id": "farm001",
  "crop": { "code": "01001", "name": "맥주보리" },
  "compost": {
    "cattle_kg": 12.3,
    "chicken_kg": 0,
    "mixed_kg": 5.7,
    "pig_kg": 0
  },
  "fertilizer": {
    "base": [
      {
        "fertilizer_id": "abc123",
        "fertilizer_name": "복합비료 21-17-17",
        "N_ratio": 21,
        "P_ratio": 17,
        "K_ratio": 17,
        "usage_kg": 32.5,
        "bags": 1.63,
        "need_N_kg": 6.8,
        "need_P_kg": 3.1,
        "need_K_kg": 2.5,
        "shortage_P_kg": 0.4,
        "shortage_K_kg": 0.2
      }
    ],
    "additional": []
  }
}
```

필드 규칙
- compost.* 단위는 kg
- N_ratio/P_ratio/K_ratio는 성분 표기(%)
- usage_kg는 전체 면적에 해당하는 kg, bags는 포대 수
- 각 단계(밑거름, 웃거름) 추천 개수는 최대 3개

주의
- 요청 본문이 비어 있으면 `USER_DATA`의 기본 농장/토양 정보를 사용합니다.

### 2) 현재 기상
GET `/api/weather/current?station=관측소번호`

응답 예시
```json
{
  "temperature": 26.4,
  "humidity": 90.0,
  "precipitation": 0.0,
  "weather": "맑음"
}
```

### 3) 챗봇(RAG)
POST `/api/chat`

요청 예시
```json
{ "message": "배추 웃거름 시기와 양은?" }
```

응답 예시
```json
{
  "status": "success",
  "answer": "...",
  "routing": "SEARCH",
  "sources": ["문서A (p.3)", "문서B (p.7)"]
}
```

### 4) 토양 검사
GET `/api/soil/sensor?farmid=farm001`
GET `/api/soil/satellite?farmid=farm001`

응답 예시
```json
{
  "_id": "test002",
  "farmid": "farm0001",
  "tested_at": "2025-08-22T12:00:00.000Z",
  "src": "sensor",
  "result": {
    "pH": "6.4",
    "OM": "22.5",
    "EC": "1.2",
    "P": "120",
    "K": "0.55",
    "Ca": "6.8",
    "Mg": "2.1"
  }
}
```

### 5) 침입자 감지
GET `/api/intruder/recent?hours=24&farmid=farm001` (프론트엔드용 - 이미지 포함)

응답 예시
```json
{
  "farm_id": "farm001",
  "hours_filter": 24,
  "total_count": 2,
  "class_counts": {
    "human": 1,
    "wild_rabbit": 1
  },
  "data": [
    {
      "id": "0081",
      "class": "human",
      "confidence": "60%",
      "datetime": "20250822-173720",
      "datetime_iso": "2025-08-22T17:37:20",
      "farm_id": "farm001",
      "image_url": "https://yourstorage.blob.core.windows.net/images/full_20250822-173720_human.jpg"
    }
  ]
}
```

**챗봇 침입자 정보**: 별도 API 없이 `intruder_cache` 서비스가 자동으로 최근 24시간 침입자 데이터를 캐시하여 챗봇 프롬프트에 포함시킵니다.

## 프로젝트 구조(요약)

```
api/
├── app.py
├── config/
│   ├── crop_codes.py
│   ├── user_data.py
│   └── __init__.py
├── routes/
│   ├── fertilizer.py
│   ├── health.py
│   ├── weather.py
│   ├── chat.py
│   ├── soil.py
│   └── intruder.py
├── services/
│   ├── chat_service.py
│   ├── db_init.py
│   ├── qa_service.py
│   ├── routing_service.py
│   ├── soil_fertilizer_cache.py
│   ├── soil_fertilizer_service.py
│   └── weather_service.py
├── utils/
│   ├── fertilizer_recommender.py
│   ├── weather_utils.py
│   └── __init__.py
├── vectorstore/
│   ├── index.faiss
│   └── index.pkl
└── requirements.txt
```

## 운영 메모

- 로깅: 기본 INFO, 디버깅이 필요할 때만 LOG_LEVEL=DEBUG. API 키 등 민감정보는 로그에 출력하지 않습니다.
- 외부 API 장애 시: `soil_fertilizer_service.py`는 안전한 기본값으로 재시도 후, 실패 시 빈 결과를 반환합니다.
- RAG: `vectorstore/`가 필요하며 누락 시 단순 검색으로 폴백됩니다.
- 침입자 감지: MongoDB 컬렉션명은 `intrusion_info`, datetime 형식은 `YYYYMMDD-HHMMSS`
- Azure Blob: 이미지 파일명 형식은 `full_{datetime}_{class}.jpg`

프로젝트에 대한 문의사항이 있으시면 Issue를 통해 연락주세요.
