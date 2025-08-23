from flask import Flask
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv
from routes.fertilizer import fertilizer_bp
from routes.weather import weather_bp
from routes.chat import chat_bp
from routes.health import health_bp
from routes.soil import soil_bp
from routes.intruder import intruder_bp
from services.soil_fertilizer_cache import initialize_fertilizer_cache
from services.weather_service import initialize_weather_data
from services.db_init import initialize_user_data_from_db
from services.intruder_cache import initialize_intruder_cache

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
app = Flask(__name__)
CORS(app)

app.register_blueprint(health_bp)
app.register_blueprint(fertilizer_bp)
app.register_blueprint(weather_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(soil_bp)
app.register_blueprint(intruder_bp)

if __name__ == '__main__':
    # 데이터 소스 선택: env DATA_SOURCE=cosmos 일 때 CosmosDB에서 로드
    data_source = os.getenv("DATA_SOURCE", "local").lower()
    if data_source in ("cosmos", "mongo", "mongodb"):
        try:
            initialize_user_data_from_db(
                user_id=os.getenv("USER_ID"),
                farm_id=os.getenv("FARM_ID"),
                user_email=os.getenv("USER_EMAIL"),
            )
            logging.info("USER_DATA initialized from CosmosDB/MongoDB")
        except Exception as e:
            logging.error("Failed to load USER_DATA from DB: %s. Falling back to local sample.", e)

    initialize_fertilizer_cache()
    initialize_weather_data()
    initialize_intruder_cache()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1")