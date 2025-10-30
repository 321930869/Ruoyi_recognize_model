"""
OCR Web服务主启动文件
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """主启动函数"""
    # 检查环境变量文件
    env_file = project_root / '.env.example'
    if env_file.exists():
        print("加载环境变量文件...")
        from dotenv import load_dotenv
        load_dotenv(env_file)

    # 导入并启动应用
    from ocr_webservice.app import app
    from ocr_webservice.config import config

    print(f"启动OCR识别服务: {config.HOST}:{config.PORT}")
    print(f"模型路径: {config.MODEL_PATH}")

    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )


if __name__ == '__main__':
    main()
