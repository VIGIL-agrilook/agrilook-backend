from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv
from flask import request
from routes.fertilizer import fertilizer_bp
from routes.fertilizer_raw import fertilizer_raw_bp
from routes.weather import weather_bp
from routes.chat import chat_bp

load_dotenv()
app = Flask(__name__)
CORS(app)


app.register_blueprint(fertilizer_bp)
app.register_blueprint(fertilizer_raw_bp)
app.register_blueprint(weather_bp)
app.register_blueprint(chat_bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)