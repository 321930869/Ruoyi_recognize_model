# Ruoyi验证码OCR识别服务

专为若依(Ruoyi)框架验证码设计的OCR识别Web服务，支持验证码文本识别和数学表达式自动计算。

## 功能特性

- 高精度识别：专门针对若依验证码训练的OCR模型
- 数学计算：自动计算验证码中的四则运算表达式
- RESTful API：简洁的HTTP JSON接口
- 安全认证：可选的API Key认证和速率限制
- 轻量部署：基于Flask，资源占用低

## 项目结构
```
Ruoyi_recognize_model/
├── ocr_webservice/          # Python包目录
│   ├── __init__.py
│   ├── app.py              # Flask应用
│   ├── auth.py             # 认证和限流
│   ├── calculator.py       # 数学表达式计算
│   ├── config.py           # 配置管理
│   └── ocr_service.py      # OCR核心服务
├── resources/              # 资源文件目录
│   ├── model.onnx          # ONNX模型文件
│   └── vocab.txt           # 词汇表文件
├── scripts/                # 部署脚本
│   └── deploy.sh
├── .env.example           # 环境变量示例
├── requirements.txt        # Python依赖
├── run.py                 # 服务启动入口
└── README.md              # 项目文档
```

## 快速开始

### 环境要求
- Python 3.7+
- 至少2GB可用内存

### 安装步骤
```bash
# 克隆项目
git clone <项目地址>
cd Ruoyi_recognize_model

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
# 编辑 .env 文件设置你的配置

# 启动服务
python run.py
```

服务将在 http://localhost:2334 启动

## 配置说明

编辑 `.env` 文件进行配置：

```bash
# 服务配置
OCR_HOST=0.0.0.0
OCR_PORT=5000
OCR_DEBUG=false

# 安全配置
OCR_API_KEY=your_secret_key_here
OCR_RATE_LIMIT=100

# 功能配置
OCR_ENABLE_CALCULATION=true
```

## API接口

### 1. 服务状态检查
```
GET /health
```

### 2. OCR识别接口
```
POST /recognize
Content-Type: application/json
X-API-Key: your_secret_key_here

{
  "image": "base64编码的图片数据",
  "calculate": true
}
```

**响应示例**
```json
{
  "success": true,
  "text": "4*0=?",
  "processing_time": 0.125,
  "calculation": {
    "success": true,
    "result": 0,
    "expression": "4*0=?"
  }
}
```

## 客户端调用示例

### Python调用
```python
import requests
import base64

def recognize_captcha(image_path, api_key, calculate=True):
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    response = requests.post(
        "http://localhost:5000/recognize",
        headers={"X-API-Key": api_key},
        json={"image": image_data, "calculate": calculate}
    )
    return response.json()

# 使用示例
result = recognize_captcha("captcha.png", "your_api_key")
```

### cURL调用
```bash
curl -X POST http://localhost:5000/recognize \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_data", "calculate": true}'
```

## 生产环境部署

### 使用Gunicorn
```bash
pip install gunicorn
gunicorn -w 1 -b 0.0.0.0:5000 run:app
```

### Systemd服务配置
创建 `/etc/systemd/system/ruoyi-ocr.service`：
```ini
[Unit]
Description=Ruoyi OCR Recognition Service
After=network.target

[Service]
Type=simple
User=ocruser
WorkingDirectory=/opt/Ruoyi_recognize_model
ExecStart=/opt/Ruoyi_recognize_model/venv/bin/gunicorn -w 1 -b 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable ruoyi-ocr
sudo systemctl start ruoyi-ocr
```

## 故障排除

### 常见问题
1. **模型加载失败**：检查resources目录下的模型文件是否存在
2. **认证失败**：确认API Key正确且在请求头中设置
3. **内存不足**：减少并发请求数或增加服务器内存

查看日志：
```bash
python run.py > service.log 2>&1
```

## 技术支持

如有问题请提交Issue或通过邮件联系。