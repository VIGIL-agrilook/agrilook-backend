# 🌾 한국 농업 토양-비료 처방 API 시스템

농촌진흥청 공공데이터를 활용한 지능형 비료 처방 시스템입니다.

## ✨ 주요 기능

- **토양 분석 기반 비료 처방**: 토양의 pH, 유기물, 유효인산 등을 분석하여 맞춤형 비료 추천
- **작물별 처방**: 252개 작물에 대한 세밀한 비료 처방 지원
- **농업 표준 단위**: a(아르) 단위 사용으로 농업 현장 친화적
- **실용적 정보**: 구체적인 비료 제품명, 사용량, 포대수 제공
- **AI 챗봇**: 농업 표준 단위(a, 아르) 기반 전문 상담 서비스

## 🛠 기술 스택

- **Backend**: Python Flask
- **AI/ML**: LangChain, OpenAI GPT-4
- **API**: 농촌진흥청 공공데이터포털 (농업기술실용화재단_비료·퇴비 정보)
- **Vector DB**: FAISS + BM25 하이브리드 검색
- **Data**: 172개 비료 제품 DB + 252개 작물 코드

## 📦 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone [repository-url]
cd api
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
cp example.env .env
# .env 파일을 열어 API 키 설정
```

### 5. 서버 실행
```bash
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
