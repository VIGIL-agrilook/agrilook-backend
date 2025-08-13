# 🌾 농업 토양-비료 처방 API 시스템

한국 공공데이터포털의 비료·퇴비 정보 API를 활용한 농업 토양 분석 및 맞춤형 비료 처방 시스템입니다.

## 🏗️ 프로젝트 구조

```
api/
├── app.py                      # Flask 메인 애플리케이션
├── soil_fertilizer_service.py  # 핵심 비료 처방 서비스
├── csv_to_json.py             # 비료 데이터베이스 변환 유틸리티
├── config/
│   ├── __init__.py
│   └── user_data.py           # 사용자 농장 데이터 (DB 대체)
├── services/                  # 기존 챗봇 서비스들
│   ├── __init__.py
│   ├── qa_service.py
│   └── routing_service.py
├── 밑거름.csv / 밑거름.json    # 밑거름 비료 데이터베이스
├── 웃거름.csv / 웃거름.json    # 웃거름 비료 데이터베이스
└── requirements.txt           # Python 패키지 의존성
```

## 🚀 주요 기능

### 1. 토양 분석 및 비료 처방
- **농장 정보**: 작물, 농장 크기(a 단위), 토양 화학성 분석
- **API 연동**: 농업기술실용화재단 비료·퇴비 정보 API 호출
- **맞춤형 처방**: 토양 상태에 따른 밑거름/웃거름 NPK 처방량 계산

### 2. 실용적 비료 추천
- **비료 데이터베이스**: 137개 밑거름, 35개 웃거름 제품 정보
- **NPK 매칭**: 질소 함량 기준 최적 비료 제품 추천 (각 3개씩)
- **사용량 계산**: 농장 크기에 맞는 구체적 사용량 및 포대수 계산
- **부족분 안내**: 인산/칼리 추가 필요량 표시

### 3. 퇴비 처방
- **퇴비 종류**: 우분퇴비, 돈분퇴비, 계분퇴비, 혼합퇴비
- **농장 규모 계산**: kg 단위 및 톤 단위 환산

## 📡 API 엔드포인트

### 토양-비료 처방 API
```
GET/POST /api/fertilizer-prescription
```

**응답 예시:**
```json
{
  "status": "success",
  "farm_info": {
    "crop_name": "맥주보리",
    "crop_code": "01001",
    "farm_size_a": 250,
    "farm_size_10a": 25.0
  },
  "fertilizer_prescription": {
    "standard_per_1000sqm": {
      "base": {"N": 4.9, "P": 24.8, "K": 3.0},
      "additional": {"N": 3.2, "P": 0.0, "K": 0.0}
    },
    "total_farm_needs": {
      "base": {"N": 122.5, "P": 620.0, "K": 75.0},
      "additional": {"N": 80.0, "P": 0.0, "K": 0.0}
    }
  },
  "compost_recommendations": {
    "cattle_compost": {"kg": 37500.0, "tons": 37.5},
    "pig_compost": {"kg": 8250.0, "tons": 8.2},
    "chicken_compost": {"kg": 6375.0, "tons": 6.4},
    "mixed_compost": {"kg": 13525.0, "tons": 13.5}
  },
  "fertilizer_recommendations": {
    "base_fertilizers": [
      {
        "name": "Eco-sol",
        "npk": "N-3% P-15% K-43%",
        "usage_kg": 4083.3,
        "bags": 204.2,
        "shortage_p": 7.5,
        "shortage_k": 0
      }
    ],
    "additional_fertilizers": [
      {
        "name": "칼슘요소",
        "npk": "N-30% P-0% K-1%",
        "usage_kg": 266.7,
        "bags": 13.3
      }
    ]
  }
}
```

## 🔧 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
`.env` 파일 생성:
```
FERTILIZER_API_KEY=your_api_key_here
```

### 3. 비료 데이터베이스 초기화
```bash
python csv_to_json.py
```

### 4. 서버 실행
```bash
python app.py
```

서버는 `http://localhost:5000`에서 실행됩니다.

## 🧪 테스트

### 독립 실행 테스트
```bash
python soil_fertilizer_service.py
```

### API 테스트
```bash
curl -X GET "http://localhost:5000/api/fertilizer-prescription"
```

## 🎯 주요 특징

- **흙토람 스타일**: 농촌진흥청 토양환경정보시스템과 유사한 출력 형태
- **실용성 중심**: 구체적인 제품명, 사용량, 포대수 제공
- **농업 표준**: a(아르) 단위 사용으로 농업 현장 친화적
- **확장성**: 실제 데이터베이스 연동 준비 완료

## 📊 데이터 구조

### 농장 정보 (config/user_data.py)
- 농장 크기: 250a (25,000㎡)
- 작물: 맥주보리 (코드: 01001)
- 토양 화학성: pH, 유기물, 유효인산, 치환성 양분 등

### 비료 데이터베이스
- **밑거름**: 137개 제품 (N-P-K 성분, 1포대당 무게 등)
- **웃거름**: 35개 제품 (주로 질소 중심 추비)

## 🌐 API 연동

현재는 테스트 데이터로 동작하며, 실제 공공데이터포털 API 연동시:
- `call_fertilizer_api()` 메서드의 주석 해제
- API 키 설정
- XML 응답 자동 파싱

---

*이 시스템은 한국의 농업 현실에 맞춘 실용적인 비료 처방 서비스를 제공합니다.*
