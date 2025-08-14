"""
기상청 API 서비스
농업 맞춤형 기상 정보 제공
"""
import os
import requests
from config.user_data import USER_DATA

class WeatherService:
    def __init__(self):
        self.base_url = "https://apihub.kma.go.kr/api/typ01/url"
        self.auth_key = os.getenv("KMA_API_KEY")

    def get_current_weather(self, station: str = None):
        import logging
        if station is None:
            station = USER_DATA["location"]["station"]
        try:
            url = f"{self.base_url}/kma_sfctm2.php"
            params = {
                'stn': station,
                'help': 1,
                'authKey': self.auth_key
            }
            response = requests.get(url, params=params, timeout=30)
            logging.info(f"KMA API Request URL: {url} | Params: {params}")
            logging.info(f"KMA API Response Status: {response.status_code}")
            logging.info(f"KMA API Response Text: {response.text[:500]}")
            response.raise_for_status()
            lines = response.text.strip().split('\n')
            target_station_data = None
            for line in lines:
                if line and not line.startswith('#') and len(line) > 20:
                    # 관측소 번호가 포함된 라인을 직접 검색
                    if str(station) in line:
                        target_station_data = line
                        break
            if not target_station_data:
                logging.error(f"No data found for station {station}")
                return None
            parsed = self._parse_fixed_width_data(target_station_data)
            return parsed
        except Exception as e:
            logging.error(f"Weather API error: {e}")
            return None

    def _parse_fixed_width_data(self, line: str):
        parts = line.split()
        if len(parts) < 16:
            return None
        temperature = float(parts[11]) if len(parts) > 11 else None
        humidity = float(parts[13]) if len(parts) > 13 else None
        ca_tot = float(parts[14]) if len(parts) > 14 else None  # CA_TOT (구름량)
        precipitation = float(parts[10]) if len(parts) > 10 else None  # RN (강수량)
        return {
            'temperature': temperature,
            'humidity': humidity,
            'precipitation': precipitation,
            'ca_tot': ca_tot
        }

weather_service = WeatherService()
