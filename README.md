# 🌾 한국 농업 다중작물 비료 추천 시스템

> **최신 업데이트**: 다중 작물 처리 시스템으로 업그레이드! 최대 3작물을 동시 처리하여 종합적인 농장 관리가 가능합니다.

농촌진흥청 공공데이터와 기상청 API를 활용한 지능형 다중작물 비료 처방 시스템입니다.

## ✨ 주요 기능

### 🌱 다중 작물 처리
- **동시 처리**: 최대 3작물을 한 번에 분석하여 종합적인 비료 처방 제공
- **작물별 맞춤 처방**: 각 작물의 생육 단계와 특성을 고려한 개별 처방
- **상호작용 분석**: 작물 간 영양소 경합 및 윤작 고려

### 🌦️ 스마트 기상 연동
- **실시간 기상 데이터**: 한국기상청(KMA) API 연동
- **위치 기반 처방**: 구리시 기준 관측소(108) 데이터 활용
- **날씨 기반 조정**: 기온, 강수량, 습도 등을 고려한 비료 사용량 조정

### 🧪 정밀 토양 분석
- **토양 성분 분석**: pH, 유기물, 유효인산, 치환성 칼리 등 종합 분석
- **토양 개선 처방**: 토양 조건에 맞는 퇴비 및 개량제 추천
- **농업 표준 단위**: a(아르) 단위 사용으로 농업 현장 친화적

### 🎯 실용적 정보 제공
- **구체적 제품명**: 172개 등록된 비료 제품 중 최적 선택
- **정확한 사용량**: 포대수 단위까지 정밀 계산
- **시기별 처방**: 밑거름, 웃거름 구분 및 시용 시기 안내

## 🛠 기술 스택

- **Backend**: Python Flask, CORS 지원
- **AI/ML**: LangChain, OpenAI GPT-4
- **데이터 처리**: Pandas, NumPy
- **API 연동**: 
  - 농촌진흥청 공공데이터포털 (비료·퇴비 정보)
  - 한국기상청 (날씨 정보)
- **Vector DB**: FAISS + BM25 하이브리드 검색
- **데이터베이스**: 
  - 300+ 작물 코드 매핑
  - 172개 비료 제품 정보
  - 토양 분석 기준 데이터

## 📦 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone https://github.com/VIGIL-agrilook/agrilook-backend.git
cd agrilook-backend
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux  
source .venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
```bash
# example.env를 .env로 복사
cp example.env .env

# .env 파일에서 API 키 설정
# - PUBLIC_DATA_API_KEY: 공공데이터포털에서 발급
# - KMA_API_KEY: 기상청 API 허브에서 발급  
# - OPENAI_API_KEY: OpenAI에서 발급
```

### 5. 서버 실행
```bash
python app.py
```

서버가 `http://localhost:5000`에서 실행됩니다.

## 🚀 API 사용법


### 단일 작물 비료 추천
```bash
POST /api/fertilizer-recommendation
Content-Type: application/json

{
  "cropName": "맥주보리",
  "fieldId": "farm001",
  "area_sqm": 25000
}
```

**응답 예시:**
```json
{
  "status": "success",
  "crop": { "code": "01001", "name": "맥주보리" },
  "field": { "id": "farm001", "area_sqm": 25000 },
  "fertilizer": {
    "base": [
      {
        "fertilizer_id": "base_002",
        "fertilizer_name": "Eco-sol",
        "N_ratio": 0.43,
        "P_ratio": 0.15,
        "K_ratio": 0.03,
        "bags": 204.2,
        "need_N_kg": 122.5,
        "need_P_kg": 620.0,
        "need_K_kg": 75.0,
        "shortage_P_kg": 7.5,
        "shortage_K_kg": 0,
        "usage_kg": 4083.3
      }
    ],
    "additional": [ ... ]
  },
  "compost": {
    "cattle_kg": 37500.0,
    "chicken_kg": 6375.0,
    "mixed_kg": 12200.0,
    "pig_kg": 8250.0
  }
}
```

### 현재 날씨 정보
```bash
GET /api/weather/current
```
**응답 예시:**
```json
{
  "status": "success",
  "data": {
    "temperature": 26.4,
    "humidity": 90.0,
    "precipitation": 0.0,
    "weather": "sunny"
  }
}
```

### 농업 AI 챗봇
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "250a 농장에서 콩과 보리를 함께 재배할 때 주의사항은?"
}
```

## 📊 지원 작물

### 주요 작물 카테고리 (300+ 품목)
- **식량작물**: 벼, 보리, 콩, 옥수수 등
- **채소류**: 배추, 무, 양파, 고추 등  
- **과수류**: 사과, 배, 포도, 감귤 등
- **특용작물**: 참깨, 들깨, 땅콩 등
- **화훼류**: 국화, 장미, 백합 등

전체 작물 목록은 `config/crop_codes.py`에서 확인 가능합니다.

## 🏗 프로젝트 구조

```
agrilook-backend/
├── app.py                      # Flask 메인 애플리케이션
├── requirements.txt            # 패키지 의존성
├── example.env                 # 환경변수 예시
├── .gitignore                 # Git 제외 파일
│
├── config/                    # 설정 파일
│   ├── user_data.py          # 사용자 농장 데이터
│   ├── crop_codes.py         # 300+ 작물 코드 매핑
│   └── __init__.py
│
├── services/                  # 비즈니스 로직
│   ├── multiple_crop_service.py      # 다중작물 처리 서비스
│   ├── soil_fertilizer_service.py    # 토양 비료 분석 서비스
│   ├── weather_service.py           # 기상 데이터 서비스
│   ├── qa_service.py               # AI 챗봇 서비스
│   └── routing_service.py          # 라우팅 서비스
│
├── utils/                     # 유틸리티 함수
│   ├── crop_mapper.py        # 작물 매핑 유틸
│   ├── weather_utils.py      # 날씨 데이터 처리
│   └── __init__.py
│
├── vectorstore/              # 벡터 검색 DB
│   ├── index.faiss          # FAISS 인덱스
│   └── index.pkl            # 메타데이터
│
└── deploy/                   # 배포 설정
    ├── azure/               # Azure 배포
    └── scripts/            # 배포 스크립트
```

## 🔧 주요 서비스 모듈

### MultipleCropFertilizerService
- **역할**: 최대 3작물 동시 처리 및 종합 처방
- **기능**: 작물별 개별 분석 + 상호작용 고려 + 비용 최적화

### SoilFertilizerService  
- **역할**: 토양 분석 및 정밀 비료 계산
- **기능**: 172개 비료 제품 중 최적 선택 + 사용량 계산

### WeatherService
- **역할**: 실시간 기상 데이터 연동
- **기능**: 구리시 기준 날씨 정보 + 비료 사용량 조정

## 🌐 배포

### 개발 환경
```bash
export FLASK_ENV=development
python app.py
```

### 프로덕션 환경
```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

## 📋 API 키 발급

### 1. 공공데이터포털 (필수)
- [데이터포털 접속](https://www.data.go.kr)
- "농업기술실용화재단_비료·퇴비 정보" 검색
- API 신청 및 승인 후 키 발급

### 2. 기상청 API (필수)  
- [기상청 API허브](https://apihub.kma.go.kr) 접속
- 회원가입 후 API 키 발급
- 단기예보 및 실시간 관측 서비스 신청

### 3. OpenAI API (선택)
- [OpenAI Platform](https://platform.openai.com) 접속
- API 키 발급 (AI 챗봇 기능용)

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 `LICENSE` 파일을 참고하세요.

## 👥 개발팀

**VIGIL-agrilook** - 한국 스마트농업 솔루션 개발팀

## 📞 지원

- **이슈 신고**: [GitHub Issues](https://github.com/VIGIL-agrilook/agrilook-backend/issues)
- **기술 문의**: 프로젝트 Issues를 통해 문의해주세요
- **기능 제안**: Pull Request 또는 Issues로 제안해주세요

---

**💡 Tip**: 시작하기 전에 `example.env`를 참고하여 필요한 API 키를 준비해주세요!

**🔥 최신 기능**: 이제 한 번의 요청으로 농장 전체의 다중작물 비료 처방을 받을 수 있습니다!
python app.py
```

## 🔧 환경변수

`.env` 파일에 다음 변수들을 설정하세요:

```env
# 공공데이터포털 API 키
PUBLIC_DATA_API_KEY=your_api_key_here

# OpenAI API 키 (챗봇 기능용)
OPENAI_API_KEY=your_openai_key_here

# Flask 설정
FLASK_ENV=development
FLASK_DEBUG=True
```

## 📡 API 엔드포인트

### 1. 작물 목록 조회
```
GET /api/crops
```

### 2. 비료 처방 (작물 선택)
```
POST /api/fertilizer-prescription
Content-Type: application/json

{
  "crop_name": "토마토(시설)",
  "soil": {
    "ph": 6.5,
    "om": 25,
    "vldpha": 300,
    "posifert_K": 0.8,
    "posifert_Ca": 6.0,
    "posifert_Mg": 2.5,
    "selc": 1.5
  }
}
```

### 3. 비료 처방 테스트 (기본 작물)
```
GET /api/fertilizer-prescription/test
```

### 4. 현재 기상 정보 (간편 조회)
```
GET /api/weather/current?station=108
```

**응답 예시:**
```json
{
  "status": "success",
  "data": {
    "temperature": 28.5,
    "precipitation": 0,
    "humidity": 65,
    "location": "서울",
    "last_updated": "2025-08-13T14:30:00",
    "summary": "현재 서울 지역 기온 28.5°C, 습도 65%, 강수 없음"
  }
}
```

### 5. 기상 데이터 업데이트
```
POST /api/weather/update
Content-Type: application/json

{
  "station": "108"
}
```

### 6. 농업 맞춤 기상 요약
```
GET /api/weather/agricultural-summary?station=108
```

**주요 관측지점:**
- 서울: 108
- 인천: 112  
- 수원: 119
- 춘천: 101
- 강릉: 105

### 7. AI 챗봇 (농업 전문 상담)
```
POST /chat
Content-Type: application/json

{
  "message": "250a 농장에서 토마토 재배할 때 필요한 비료량은?"
}
```

**응답 예시:**
- 농업 표준 단위 사용 (a, 아르)
- 구체적인 제품명과 포대수 안내
- 토양 조건별 맞춤 조언

## 📊 지원 작물

총 252개 작물 지원 (농촌진흥청 공식 작물코드 기준)

- **식량작물**: 벼, 맥주보리, 밀, 보리, 옥수수, 콩 등
- **과채류**: 토마토, 고추, 오이, 수박, 딸기 등
- **엽채류**: 배추, 상추, 시금치, 브로콜리 등
- **근채류**: 무, 당근, 마늘, 양파 등
- **과수류**: 사과, 배, 포도, 감귤, 복숭아 등
- **특용작물**: 인삼, 도라지, 더덕 등

## 📁 프로젝트 구조

```
api/
├── app.py                    # Flask 메인 애플리케이션
├── requirements.txt          # Python 패키지 의존성
├── example.env              # 환경변수 템플릿
├── config/                  # 설정 파일들
│   ├── __init__.py
│   ├── user_data.py        # 사용자 데이터 설정
│   └── crop_codes.py       # 252개 작물 코드 매핑
├── services/                # 서비스 로직
│   ├── __init__.py
│   ├── soil_fertilizer_service.py  # 토양-비료 API 서비스
│   ├── qa_service.py       # QA 서비스
│   ├── routing_service.py  # 라우팅 서비스
│   └── chat_service.py     # AI 챗봇 서비스
├── data/                   # 데이터 파일들
│   ├── README.md          # 데이터 설명
│   ├── 밑거름.json        # 기비 데이터 (137개 제품)
│   └── 웃거름.json        # 추비 데이터 (35개 제품)
├── utils/                  # 유틸리티 및 개발 도구
│   ├── __init__.py
│   └── csv_to_json.py     # CSV → JSON 변환 도구
├── vectorstore/           # 벡터 데이터베이스
│   ├── index.faiss       # FAISS 벡터 인덱스
│   └── index.pkl         # 벡터 메타데이터
└── deploy/               # 배포 관련
    ├── azure/           # Azure 배포 설정
    └── scripts/         # 배포 스크립트
```

## 🎯 주요 특징

- **정확한 처방**: 농촌진흥청 토양환경정보시스템 기준
- **실용적 정보**: 구체적인 제품명과 사용량 (kg, 포대 수)
- **농업 친화적**: a(아르) 단위 사용
- **다양한 작물**: 252개 작물별 맞춤 처방
- **AI 상담**: 농업 표준 단위(a) 기반 전문 지식 챗봇

## 📄 라이선스

이 프로젝트는 MIT 라이선스하에 배포됩니다.

## 🤝 기여

버그 리포트, 기능 제안, 코드 기여를 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 Issue를 통해 연락주세요.
