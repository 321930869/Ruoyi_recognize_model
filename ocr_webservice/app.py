from flask import Flask
from .config import config


def create_app():
    """创建Flask应用工厂函数"""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

    # 注册路由
    from .routes import bp
    app.register_blueprint(bp)

    return app


# 创建默认应用实例
app = create_app()