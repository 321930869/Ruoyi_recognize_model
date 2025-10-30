import os
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


class Config:
    """应用配置类"""

    @property
    def HOST(self):
        return os.getenv('OCR_HOST', '0.0.0.0')

    @property
    def PORT(self):
        return int(os.getenv('OCR_PORT', '5000'))

    @property
    def DEBUG(self):
        return os.getenv('OCR_DEBUG', 'false').lower() == 'true'

    @property
    def MODEL_PATH(self):
        return os.getenv(f'{PROJECT_ROOT}/OCR_MODEL_PATH', str(PROJECT_ROOT / 'resources' / 'model.onnx'))

    @property
    def VOCAB_PATH(self):
        return os.getenv('OCR_VOCAB_PATH', str(PROJECT_ROOT / 'resources' / 'vocab.txt'))

    @property
    def API_KEY(self):
        return os.getenv('OCR_API_KEY', '')

    @property
    def RATE_LIMIT(self):
        return int(os.getenv('OCR_RATE_LIMIT', '100'))

    @property
    def MAX_CONTENT_LENGTH(self):
        return 16 * 1024 * 1024

    @property
    def LOG_LEVEL(self):
        return os.getenv('OCR_LOG_LEVEL', 'INFO')

    @property
    def ENABLE_CALCULATION(self):
        return os.getenv('OCR_ENABLE_CALCULATION', 'true').lower() == 'true'


# 创建配置实例
config = Config()
