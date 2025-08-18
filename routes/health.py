from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "농업 AI 시스템이 정상 작동 중입니다.",
        "version": "1.0.0"
    })

health_check = Blueprint('health_check', __name__)

@health_check.route('/health')
def health():
    return 'OK'
