import time
from functools import wraps
from flask import request, jsonify
from collections import defaultdict
import logging

logger = logging.getLogger('Auth')


class RateLimiter:
    """简单的速率限制器"""

    def __init__(self):
        self.requests = defaultdict(list)

    def is_limited(self, identifier: str, max_requests: int, window_seconds: int = 86400) -> bool:
        """检查是否超过限制"""
        now = time.time()
        window_start = now - window_seconds

        # 清理过期请求
        self.requests[identifier] = [req_time for req_time in self.requests[identifier]
                                     if req_time > window_start]

        # 检查限制
        if len(self.requests[identifier]) >= max_requests:
            return True

        # 记录本次请求
        self.requests[identifier].append(now)
        return False


# 全局限流器实例
rate_limiter = RateLimiter()


def require_auth(f):
    """API认证装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .config import config

        # 如果未配置API_KEY，则跳过认证
        if not config.API_KEY:
            return f(*args, **kwargs)

        provided_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if not provided_key or provided_key != config.API_KEY:
            logger.warning(f"认证失败: 提供的Key: {provided_key}")
            return jsonify({
                "success": False,
                "error": "认证失败: 无效的API Key"
            }), 401

        return f(*args, **kwargs)

    return decorated_function


def rate_limit(f):
    """速率限制装饰器"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .config import config

        # 获取客户端标识（IP或API Key）
        identifier = request.headers.get('X-API-Key') or request.remote_addr

        if rate_limiter.is_limited(identifier, config.RATE_LIMIT):
            logger.warning(f"速率限制: {identifier}")
            return jsonify({
                "success": False,
                "error": "请求频率超限，请稍后重试"
            }), 429

        return f(*args, **kwargs)

    return decorated_function
