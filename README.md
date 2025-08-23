## 들여다밭(Agrilook) 백엔드 API

**팀: vigil**

## 📋 서비스 개요

농업 전문 지식 검색과 개인 맞춤형 농장 관리를 제공하는 AI 어시스턴트 시스템입니다.

### 🎯 주요 기능

#### 1. 🤖 AI 챗봇 (핵심 기능)
- **POST** `/api/chat`
- **지능형 라우팅**: 질문 유형을 자동 분류 (SEARCH/DIRECT)
- **SEARCH**: 농업 전문 문서 검색 기반 답변 (폭염 대응, 병충해 방제 등)
- **DIRECT**: 개인 농장 데이터 기반 답변 (비료 추천, 토양 정보 등)

#### 2. 🧪 비료 추천 시스템
**POST** `/api/fertilizer-recommendation`
```json
// 요청
{
  "cropname": "고추",
  "farmid": "farm001"  // 선택사항
}

// 응답
{
  "status": "success",
  "crop": {
    "name": "고추",
    "code": "01001"
  },
  "compost": {
    "cattle_kg": 1500,
    "chicken_kg": 500,
    "pig_kg": 300,
    "mixed_kg": 200
  },
  "fertilizer": {
    "base": [
      {
        "fertilizer_name": "복합비료 14-14-14",
        "N_ratio": 14, "P_ratio": 14, "K_ratio": 14,
        "usage_kg": 25.5, "bags": 1.28,
        "shortage_P_kg": 2.1, "shortage_K_kg": 1.8
      }
    ],
    "additional": [
      {
        "fertilizer_name": "요소",
        "N_ratio": 46, "P_ratio": 0, "K_ratio": 0,
        "usage_kg": 15.2, "bags": 0.76,
        "shortage_P_kg": 0, "shortage_K_kg": 8.5
      }
    ]
  }
}
```

#### 3. 🌤️ 기상 정보
**GET** `/api/weather/current?station=108`
```json
// 응답
{
  "status": "success",
  "station": 108,
  "temperature": 25.3,
  "humidity": 65,
  "precipitation": 0,
  "weather": "맑음",
  "timestamp": "2025-08-25T14:30:00Z"
}
```

#### 4. 🛡️ 농장 관리

**토양 검사**
```bash
GET /api/soil/sensor    # 센서 기반 데이터
GET /api/soil/satellite # 위성 기반 데이터
```
```json
// 응답
{
  "status": "success", 
  "source": "sensor",
  "tested_at": "2025-07-01T09:00:00Z",
  "result": {
    "pH": 6.5,
    "OM": 22.0,    // 유기물 g/kg
    "EC": 6.0,     // 전기전도도 dS/m
    "P": 10.0,     // 유효인산 mg/kg
    "K": 4.0,      // 치환성칼리 cmol+/kg
    "Ca": 6.0,     // 치환성칼슘 cmol+/kg
    "Mg": 13.0     // 치환성마그네슘 cmol+/kg
  }
}
```

**침입자 감지**
```bash
GET /api/intruder/recent
```
```json
// 응답
{
  "status": "success",
  "summary": {
    "total_detections": 5,
    "classes": {
      "멧돼지": 3,
      "고라니": 2
    }
  },
  "recent_detections": [
    {
      "class": "멧돼지",
      "confidence": "95%", 
      "datetime": "20250825-143022",
      "image_url": "https://storage.blob.core.windows.net/images/detection_001.jpg"
    }
  ]
}
```

## 🚀 빠른 시작

### 1️⃣ 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp example.env .env
# .env 파일에서 필요한 API 키들을 설정하세요
```

### 2️⃣ 서버 실행
```bash
python app.py
# 서버가 http://localhost:5001 에서 실행됩니다
```

## 🧠 AI 챗봇 사용법

### SEARCH 모드 (농업 전문 지식)
```json
POST /api/chat
{
  "message": "폭염일 때 농사에서 가장 중요한 부분이 뭘까요?"
}
```

**응답 예시:**
```json
{
  "answer": "폭염 시기에는 작물별 맞춤형 물 관리와 시설 온도 조절이 가장 중요합니다...",
  "routing": "SEARCH", 
  "sources": [
    "1. 폭염·폭우·태풍 대비 농작업 (p.4-5)",
    "2. 주요 농사기술-1 (p.7-8)"
  ],
  "status": "success"
}
```

### DIRECT 모드 (개인 농장 관리)
```json
POST /api/chat
{
  "message": "고추 비료 추천 내역 뽑아주세요"
}
```

## 📚 문서 데이터베이스

시스템에 포함된 농업 전문 문서들:
- 🌶️ **농업기술길잡이**: 고추, 부추, 파 재배 매뉴얼
- 📅 **주간농사정보**: 시기별 농작업 가이드
- 🚜 **주요 농사기술**: 종합 농업 기술 가이드
- 🌡️ **폭염·폭우·태풍 대비**: 기상 재해 대응 매뉴얼

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   사용자 질문    │ ─→ │  지능형 라우터   │ ─→ │   답변 생성     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼────────┐  ┌───────▼────────┐
            │ SEARCH 모드     │  │ DIRECT 모드     │
            │                │  │                │
            │ • 벡터 검색     │  │ • 농장 데이터   │
            │ • 문서 검색     │  │ • 비료 추천     │
            │ • 전문 지식     │  │ • 토양 정보     │
            └────────────────┘  └────────────────┘
```

## 🔧 기술 스택

- **Backend**: Flask, Python 3.10+
- **AI/ML**: LangChain, FAISS, SentenceTransformers
- **Database**: MongoDB (CosmosDB), Azure Blob Storage
- **APIs**: 농촌진흥청 비료 API, 기상청 API

## 📄 전체 API 엔드포인트

| 엔드포인트 | 메서드 | 기능 | 파라미터 |
|-----------|--------|------|----------|
| `/api/health` | GET | 서버 상태 확인 | - |
| `/api/chat` | POST | AI 챗봇 (핵심 기능) | `{"message": "질문"}` |
| `/api/fertilizer-recommendation` | POST | 비료 추천 | `{"cropname": "고추"}` |
| `/api/weather/current` | GET | 기상 정보 | `?station=108` |
| `/api/soil/sensor` | GET | 센서 토양 검사 | - |
| `/api/soil/satellite` | GET | 위성 토양 검사 | - |
| `/api/intruder/recent` | GET | 침입자 감지 현황 | - |

## 📋 환경 변수

### 필수 API 키
```env
# 비료 처방을 위한 공공데이터포털 API 키 (필수)
FERTILIZER_API_KEY=your_fertilizer_api_key_here

# 기상청 API 키 (필수)
KMA_API_KEY=your_kma_api_key_here

# OpenAI API 키 (임베딩용, 선택)
OPENAI_API_KEY=your_openai_api_key_here

# 챗봇 사용을 위한 API 키
ADOTX_API_KEY=your_adotx_api_key_here
BASE_URL=https://guest-api.sktax.chat/v1
```

### 데이터베이스 설정
```env
# 데이터 소스 선택: local | cosmos | mongo | mongodb
DATA_SOURCE=mongo

# CosmosDB(Mongo API) 접속 정보
MONGO_URI=mongodb://username:password@host:port/?ssl=true&replicaSet=globaldb
DB_NAME=agrilook-mongo

# 선택: 기본 사용자/농장 지정
USER_ID=user001
FARM_ID=farm001
USER_EMAIL=farmer@example.com
```

### 서버 설정
```env
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5001
FRONTEND_DOMAIN=https://your-frontend-app.azurewebsites.net

# Azure Blob Storage 설정 (침입자 이미지용)
AZURE_BLOB_BASE_URL=https://yourstorage.blob.core.windows.net/images
```

## 📊 데이터 구조

### USER_DATA 스키마
```python
USER_DATA = {
    "farm": {
        "_id": "farm001",
        "name": "김농부네 농장", 
        "address": "경기도 구리시 교문동",
        "stn": 108,  # 기상 관측소 번호
        "area_m2": 25000,  # 250a = 25,000㎡
        "crops": [
            {
                "cropname": "고추",
                "planted_at": "2025-04-01T00:00:00Z",
                "status": "growing"
            }
        ]
    },
    "user": {
        "_id": "user001",
        "name": "김농부",
        "email": "farmer@example.com"
    },
    "soil": {
        "pH": 6.5,
        "OM": 22.0,    # 유기물 g/kg
        "EC": 6.0,     # 전기전도도 dS/m
        "P": 10.0,     # 유효인산 mg/kg
        "K": 4.0,      # 치환성칼리 cmol+/kg
        "Ca": 6.0,     # 치환성칼슘 cmol+/kg
        "Mg": 13.0     # 치환성마그네슘 cmol+/kg
    },
    "location": {
        "station": 108,
        "address": "경기도 구리시 교문동",
        "coord": {"lon": 127.1295, "lat": 37.5943}
    },
    "weather": {},  # 실시간 업데이트
    "intruders": [] # 최근 24시간 감지 데이터
}
```

## 🔧 고급 설정

### 벡터스토어 관리
```bash
# 전체 재빌드 (문서 변경 시)
python scripts/build_vectorstore.py

# 새 문서만 추가 
python scripts/build_vectorstore.py --append
```

### 비료 캐시 최적화
- 시스템 시작 시 자동으로 작물별 비료 추천 캐시 생성
- 캐시 키: `{farm_id}_{cropname}`
- 실패 시 에러 상태 기록으로 디버깅 지원

### 침입자 감지 설정
- 24시간 내 감지 데이터 자동 캐시
- Azure Blob Storage 이미지 URL 연동
- 클래스별 카운트 및 신뢰도 정보 제공

## 🔍 디버깅

### 로그 레벨 설정
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### 일반적인 문제들

**1. CosmosDB 연결 실패**
- MONGO_URI 형식 확인
- IP 화이트리스트 설정
- SSL 인증서 문제

**2. 벡터스토어 로딩 실패**
- 임베딩 모델 다운로드 대기
- SentenceTransformer 모델 자동 다운로드

**3. API 키 오류**
- `.env` 파일 경로 확인
- API 할당량 및 유효성 검증

## 🧪 테스트

### API 테스트
```bash
# 건강 체크
curl http://localhost:5001/api/health

# 챗봇 테스트
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "폭염 대응 방법 알려주세요"}'

# 비료 추천 테스트  
curl -X POST http://localhost:5001/api/fertilizer-recommendation \
  -H "Content-Type: application/json" \
  -d '{"cropname": "고추"}'
```

## 👥 팀 정보

**Team VIGIL** - 농업 AI 기술로 더 나은 농사를 지원합니다

## 📄 라이센스

이 프로젝트는 시연용으로 제작되었습니다.

---
