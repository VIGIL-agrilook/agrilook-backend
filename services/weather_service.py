"""
기상청 API 서비스
농업 맞춤형 기상 정보 제공
"""
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
from config.user_data import USER_DATA
from utils.weather_utils import parse_city_from_address, safe_float

# .env 파일 로드
load_dotenv()

# 전역 기상 변수 - 챗봇과 프론트엔드에서 공유
CURRENT_WEATHER = {
    "temperature": None,      # 기온 (°C)
    "precipitation": None,    # 강수량 (mm)
    "humidity": None,         # 상대습도 (%)
    "last_updated": None,     # 마지막 업데이트 시간
    "location": USER_DATA["location"]["name"],  # 유저 데이터에서 지역 가져오기
    "status": "disconnected"  # API 연결 상태
}


class WeatherService:
    """기상청 API Hub 서비스"""
    
    def __init__(self):
        self.base_url = "https://apihub.kma.go.kr/api/typ01/url"
        self.auth_key = os.getenv("KMA_API_KEY")  # .env에서 로드된 API 키
        
        # API 키 상태 확인
        if not self.auth_key:
            print("❌ KMA_API_KEY가 설정되지 않았습니다.")
        else:
            print(f"✅ KMA_API_KEY 설정됨: {self.auth_key[:10]}...")
        
    def get_current_weather(self, station: str = None) -> Optional[Dict]:
        """
        현재 기상 정보 조회 및 전역 변수 업데이트
        
        Args:
            station: 지점번호 (기본값: USER_DATA에서 가져오기)
            
        Returns:
            기상 정보 딕셔너리 또는 None
        """
        global CURRENT_WEATHER
        
        # 기본 관측소를 USER_DATA에서 가져오기
        if station is None:
            station = USER_DATA["location"]["station"]
        
        try:
            # 기상청 지상관측 레이더 API
            # 실시간 기온(TA), 습도(HM), 강수량(RN) 데이터 제공
            url = f"{self.base_url}/kma_sfctm2.php"
            params = {
                'stn': station,
                'help': 1,
                'authKey': self.auth_key
            }
            
            print(f"🌡️ 지상관측 레이더 API 호출: {url}")
            print(f"📋 파라미터: stn={station}, authKey={self.auth_key[:10] if self.auth_key else 'None'}...")
            
            response = requests.get(url, params=params, timeout=30)
            print(f"📡 응답 코드: {response.status_code}")
            print(f"📄 응답 내용 (처음 500자): {response.text[:500]}")
            
            response.raise_for_status()
            
            # 고정 폭 문자열 파싱 (서울 108번 관측소를 찾아서 파싱)
            lines = response.text.strip().split('\n')
            target_station_data = None
            
            for line in lines:
                if line and not line.startswith('#') and len(line) > 20:
                    # 고정 폭으로 파싱
                    try:
                        # STN(지점번호)는 13-15 위치에 있음
                        if len(line) >= 15:
                            line_station = line[13:16].strip()
                            if line_station == station:
                                target_station_data = line
                                print(f"✅ 관측소 {station} 데이터 발견: {line[:100]}...")
                                break
                    except:
                        continue
            
            if not target_station_data:
                print(f"❌ 관측소 {station} 데이터를 찾을 수 없음")
                CURRENT_WEATHER["status"] = "no_data"
                return None
            
            # 고정 폭 위치에서 데이터 추출
            formatted_data = self._parse_fixed_width_data(target_station_data, station)
            
            # 전역 변수 업데이트
            if formatted_data and formatted_data.get('status') == 'success':
                CURRENT_WEATHER.update({
                    "temperature": formatted_data.get("temperature"),
                    "precipitation": formatted_data.get("rainfall", 0),
                    "humidity": formatted_data.get("humidity"),
                    "last_updated": datetime.now().isoformat(),
                    "status": "success"
                })
                print(f"✅ 전역 기상 변수 업데이트: 기온={CURRENT_WEATHER['temperature']}°C, 습도={CURRENT_WEATHER['humidity']}%, 강수량={CURRENT_WEATHER['precipitation']}mm")
            
            return formatted_data
            
        except Exception as e:
            print(f"기상 정보 조회 오류: {e}")
            CURRENT_WEATHER["status"] = "error"
            return None
    
    def get_daily_weather(self, station: str = "108", days: int = 7) -> List[Dict]:
        """
        일별 기상 정보 조회 (최근 며칠)
        
        Args:
            station: 지점번호
            days: 조회할 일수 (기본 7일)
            
        Returns:
            일별 기상 정보 리스트
        """
        try:
            weather_list = []
            
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime("%Y%m%d")
                
                url = f"{self.base_url}/kma_sfcdd.php"
                params = {
                    'tm': date_str,
                    'stn': station,
                    'help': 1,
                    'authKey': self.auth_key
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                # CSV 파싱
                lines = response.text.strip().split('\n')
                if len(lines) >= 2:
                    headers = lines[0].split(',')
                    data = lines[1].split(',')
                    
                    daily_data = {}
                    for j, header in enumerate(headers):
                        if j < len(data):
                            daily_data[header.strip()] = data[j].strip()
                    
                    formatted_data = self._format_daily_data(daily_data)
                    if formatted_data:
                        weather_list.append(formatted_data)
            
            return weather_list
            
        except Exception as e:
            print(f"일별 기상 정보 조회 오류: {e}")
            return []
            
    def _parse_fixed_width_data(self, line: str, station: str) -> Dict:
        """
        기상청 고정 폭 데이터 파싱
        
        레이더 API 응답 형식:
        YYMMDDHHMI STN  WD   WS GST  GST  GST     PA     PS PT    PR   TA    TD    HM    PV     RN     RN     RN     RN     SD     SD     SD WC WP WW...
        202508131400  108  20  5.2  18 10.0 1351 1001.0 1010.7 -9  -9.0  26.6  25.1  92.0  31.9    0.0  112.1  112.1...
        """
        try:
            # 고정 위치에서 데이터 추출 (위치는 헤더 설명 기반)
            # TM(0-11), STN(13-15), WD(18-19), WS(21-24), ..., TA(위치 확인 필요), HM(위치 확인 필요), RN(위치 확인 필요)
            
            # 공백으로 분할해서 각 컬럼 파싱 (더 안전한 방법)
            parts = line.split()
            
            if len(parts) < 16:
                return {'status': 'error', 'message': '데이터 형식 오류'}
            
            # 데이터 위치 (0-based 인덱스)
            # 0:TM, 1:STN, 2:WD, 3:WS, 4:GST_WD, 5:GST_WS, 6:GST_TM, 7:PA, 8:PS, 9:PT, 10:PR, 11:TA, 12:TD, 13:HM, 14:PV, 15:RN, ...
            
            temperature = safe_float(parts[11]) if len(parts) > 11 else None  # TA (기온)
            humidity = safe_float(parts[13]) if len(parts) > 13 else None     # HM (습도)  
            rainfall = safe_float(parts[15]) if len(parts) > 15 else None     # RN (강수량)
            
            return {
                'observation_time': parts[0] if len(parts) > 0 else '',
                'station': parts[1] if len(parts) > 1 else station,
                'temperature': temperature,  # 기온 (°C)
                'humidity': humidity,        # 상대습도 (%)
                'rainfall': rainfall,        # 강수량 (mm)
                'wind_speed': safe_float(parts[3]) if len(parts) > 3 else None,  # 풍속
                'wind_direction': parts[2] if len(parts) > 2 else '',                  # 풍향
                'pressure': safe_float(parts[7]) if len(parts) > 7 else None,    # 현지기압
                'status': 'success'
            }
            
        except Exception as e:
            print(f"고정 폭 데이터 파싱 오류: {e}")
            print(f"문제 라인: {line[:100]}...")
            return {'status': 'error', 'message': str(e)}
    def _format_weather_data(self, data: Dict) -> Dict:
        """현재 기상 데이터 포맷팅 (레거시 - 현재 사용 안함)"""
        try:
            return {
                'observation_time': data.get('TM', ''),
                'station': data.get('STN', ''),
                'temperature': safe_float(data.get('TA', '')),  # 기온
                'humidity': safe_float(data.get('HM', '')),    # 상대습도
                'rainfall': safe_float(data.get('RN', '')),    # 강수량
                'wind_speed': safe_float(data.get('WS', '')),  # 풍속
                'wind_direction': data.get('WD', ''),               # 풍향
                'ground_temp': safe_float(data.get('TS', '')), # 지면온도
                'soil_temp_5cm': safe_float(data.get('TE_005', '')), # 5cm 지중온도
                'soil_temp_10cm': safe_float(data.get('TE_01', '')),  # 10cm 지중온도
                'pressure': safe_float(data.get('PA', '')),     # 현지기압
                'status': 'success'
            }
        except Exception as e:
            print(f"데이터 포맷팅 오류: {e}")
            return {'status': 'error', 'message': str(e)}
            
    def _format_daily_data(self, data: Dict) -> Optional[Dict]:
        """일별 기상 데이터 포맷팅"""
        try:
            return {
                'date': data.get('TM', ''),
                'station': data.get('STN', ''),
                'avg_temp': safe_float(data.get('TA_AVG', '')),     # 평균기온
                'max_temp': safe_float(data.get('TA_MAX', '')),     # 최고기온
                'min_temp': safe_float(data.get('TA_MIN', '')),     # 최저기온
                'rainfall': safe_float(data.get('RN_DAY', '')),     # 일강수량
                'avg_humidity': safe_float(data.get('HM_AVG', '')), # 평균습도
                'min_humidity': safe_float(data.get('HM_MIN', '')), # 최저습도
                'avg_wind_speed': safe_float(data.get('WS_AVG', '')), # 평균풍속
                'sunshine_hours': safe_float(data.get('SS_DAY', '')), # 일조시간
                'solar_radiation': safe_float(data.get('SI_DAY', '')), # 일사량
                'avg_ground_temp': safe_float(data.get('TS_AVG', '')), # 평균지면온도
                'soil_temp_5cm': safe_float(data.get('TE_05', '')),    # 0.5m 지중온도
            }
        except Exception as e:
            print(f"일별 데이터 포맷팅 오류: {e}")
            return None
            
    def get_agricultural_summary(self, station: str = "108") -> Dict:
        """
        농업 맞춤형 기상 요약 정보
        
        Args:
            station: 지점번호
            
        Returns:
            농업 관련 기상 요약
        """
        try:
            current = self.get_current_weather(station)
            daily_list = self.get_daily_weather(station, 7)
            
            if not current or not daily_list:
                return {'status': 'error', 'message': '기상 정보를 가져올 수 없습니다'}
            
            # 최근 7일 평균 계산
            recent_temps = [day['avg_temp'] for day in daily_list if day['avg_temp'] is not None]
            recent_rainfall = sum([day['rainfall'] for day in daily_list if day['rainfall'] is not None])
            
            avg_temp_7days = sum(recent_temps) / len(recent_temps) if recent_temps else None
            
            return {
                'status': 'success',
                'current': {
                    'temperature': current['temperature'],
                    'humidity': current['humidity'],
                    'rainfall_today': current['rainfall']
                },
                'weekly_summary': {
                    'avg_temperature_7days': round(avg_temp_7days, 1) if avg_temp_7days else None,
                    'total_rainfall_7days': round(recent_rainfall, 1),
                    'data_points': len(daily_list)
                }
            }
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _get_station_name(self, station: str) -> str:
        """관측소 코드를 이름으로 변환"""
        station_names = {
            "108": "서울",
            "112": "인천", 
            "119": "수원",
            "105": "강릉",
            "131": "청주",
            "133": "대전",
            "146": "전주",
            "156": "광주",
            "143": "대구",
            "159": "부산",
            "184": "제주"
        }
        # 구리시는 서울 관측소(108)를 사용하지만 지역명은 구리시로 표시
        if station == "108" and USER_DATA["location"]["name"] == "구리시":
            return "구리시"
        return station_names.get(station, f"관측소{station}")
    
    @staticmethod
    def parse_city_from_address(full_address: str) -> str:
        """
        전체 주소에서 시/구 정보 추출
        예: "경기도 구리시 인창동 123-45" -> "구리시"
        """
        try:
            parts = full_address.split()
            for part in parts:
                if part.endswith(('시', '구', '군')):
                    return part
            return parts[1] if len(parts) > 1 else ""
        except:
            return ""
    
    def get_weather_summary(self) -> str:
        """챗봇용 기상 요약 텍스트"""
        global CURRENT_WEATHER
        
        if CURRENT_WEATHER["status"] != "connected" or CURRENT_WEATHER["temperature"] is None:
            return "현재 기상 정보를 가져올 수 없습니다."
        
        summary = f"현재 {CURRENT_WEATHER['location']} 지역 "
        summary += f"기온 {CURRENT_WEATHER['temperature']:.1f}°C"
        
        if CURRENT_WEATHER["humidity"] is not None:
            summary += f", 습도 {CURRENT_WEATHER['humidity']:.0f}%"
        
        if CURRENT_WEATHER["precipitation"] and CURRENT_WEATHER["precipitation"] > 0:
            summary += f", 강수량 {CURRENT_WEATHER['precipitation']:.1f}mm"
        else:
            summary += ", 강수 없음"
            
        return summary
    
    def update_weather_data(self, station: str = None) -> bool:
        """기상 데이터 업데이트 (정기적으로 호출)"""
        # 기본값을 USER_DATA에서 가져오기
        if station is None:
            station = USER_DATA["location"]["station"]
        result = self.get_current_weather(station)
        return result is not None


# 전역 기상 데이터 접근 함수들
def get_current_weather_data():
    """현재 저장된 기상 데이터 반환"""
    global CURRENT_WEATHER
    return CURRENT_WEATHER.copy()

def get_weather_for_chat():
    """챗봇용 기상 요약"""
    return weather_service.get_weather_summary()


# 전역 서비스 인스턴스
weather_service = WeatherService()
