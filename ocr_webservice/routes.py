from flask import Blueprint, request, jsonify
import time
import logging

from .config import config
from .auth import require_auth, rate_limit
from .ocr_service import get_ocr_service

# 创建蓝图
bp = Blueprint('api', __name__)

# 配置日志
logger = logging.getLogger('OCRWebService')

@bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    service = get_ocr_service()
    return jsonify({
        "status": "healthy",
        "service": "OCR Recognition",
        "version": "2.0.0",
        "request_count": service.request_count,
        "calculation_enabled": config.ENABLE_CALCULATION,
        "timestamp": time.time()
    })

@bp.route('/recognize', methods=['POST'])
@require_auth
@rate_limit
def recognize():
    """OCR识别接口"""
    start_time = time.time()

    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "请求必须是JSON格式",
            "processing_time": round(time.time() - start_time, 3)
        }), 400

    data = request.get_json()

    if 'image' not in data or not data['image']:
        return jsonify({
            "success": False,
            "error": "缺少image字段或image为空",
            "processing_time": round(time.time() - start_time, 3)
        }), 400

    calculate = data.get('calculate', False)
    if not config.ENABLE_CALCULATION and calculate:
        return jsonify({
            "success": False,
            "error": "表达式计算功能未启用",
            "processing_time": round(time.time() - start_time, 3)
        }), 400

    service = get_ocr_service()
    result = service.recognize_base64(data['image'], calculate=calculate)
    result['processing_time'] = round(time.time() - start_time, 3)

    status_code = 200 if result['success'] else 500
    return jsonify(result), status_code

@bp.route('/', methods=['GET'])
def index():
    """服务首页"""
    return jsonify({
        "service": "OCR Recognition API",
        "version": "2.0.0",
        "calculation_enabled": config.ENABLE_CALCULATION,
        "endpoints": {
            "GET /health": "健康检查",
            "POST /recognize": "OCR识别（支持表达式计算）"
        }
    })