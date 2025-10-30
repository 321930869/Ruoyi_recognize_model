import base64
import io
import logging
import os
import time
from typing import Dict, Any

import cv2
import numpy as np
import onnxruntime as rt
import torch
import torch.nn.functional as F
from PIL import Image

from .calculator import calculator
from .config import config

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('OCRService')


class OCRService:
    """
    OCR服务类 - 单例模式，支持base64输入和数学计算
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """初始化OCR服务（只会执行一次）"""
        if hasattr(self, '_initialized'):
            return

        logger.info("正在初始化OCR服务...")

        # 使用配置中的路径
        self.MODEL_PATH = config.MODEL_PATH
        self.VOCAB_PATH = config.VOCAB_PATH

        # 验证文件存在
        if not os.path.exists(self.MODEL_PATH):
            raise FileNotFoundError(f"模型文件不存在: {self.MODEL_PATH}")

        # 加载模型和词汇表
        self._load_model()
        self._load_vocab()

        # 服务统计信息
        self.request_count = 0
        self._initialized = True

        logger.info("OCR服务初始化完成")

    def _load_model(self):
        """加载ONNX模型"""
        try:
            self.sess = rt.InferenceSession(self.MODEL_PATH)
            self.input_name = self.sess.get_inputs()[0].name
            self.output_name = self.sess.get_outputs()[0].name
            logger.info(f"ONNX模型加载成功: {self.MODEL_PATH}")

        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise

    def _load_vocab(self):
        """加载词汇表"""
        try:
            if os.path.exists(self.VOCAB_PATH):
                self.label_mapping = {}
                with open(self.VOCAB_PATH, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    cnt = 2
                    for line in lines:
                        line = line.strip('\n')
                        self.label_mapping[cnt] = line
                        cnt += 1
                logger.info(f"词汇表加载成功，共{len(self.label_mapping)}个字符")
            else:
                self.label_mapping = None
                logger.warning(f"词汇表文件不存在: {self.VOCAB_PATH}")

        except Exception as e:
            logger.error(f"词汇表加载失败: {e}")
            self.label_mapping = None

    def base64_to_image(self, base64_str: str) -> np.ndarray:
        """将base64字符串转换为OpenCV图像格式"""
        try:
            # 处理可能包含的data URL前缀
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]

            # 解码base64
            image_data = base64.b64decode(base64_str)
            image_bytes = io.BytesIO(image_data)

            # 使用PIL打开图像，然后转换为OpenCV格式
            pil_image = Image.open(image_bytes)

            # 转换为RGB（处理PNG的透明通道等）
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # PIL图像转换为numpy数组(RGB) -> OpenCV格式(BGR)
            cv_image = np.array(pil_image)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)

            return cv_image

        except Exception as e:
            logger.error(f"Base64解码失败: {e}")
            raise ValueError(f"无效的base64图像数据: {str(e)}")

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        预处理图像（适配base64输入）
        Args:
            image: OpenCV格式的图像 (BGR)
        Returns:
            预处理后的图像张量
        """
        target_height = 32
        target_width = 640

        # 获取图像尺寸
        h, w = image.shape[:2]

        # 计算缩放比例，保持宽高比
        scale = min(target_width / w, target_height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        # 缩放图像
        resized_img = cv2.resize(image, (new_w, new_h))

        # 创建目标尺寸的黑色背景
        padded_img = np.zeros((target_height, target_width, 3), dtype=np.uint8)
        padded_img[:new_h, :new_w, :] = resized_img

        # 归一化并转换维度
        padded_img = padded_img.astype(np.float32) / 255.0
        padded_img = np.transpose(padded_img, (2, 0, 1))  # HWC to CHW
        padded_img = np.expand_dims(padded_img, axis=0)  # 添加批次维度

        return padded_img

    def postprocess(self, preds) -> str:
        """
        后处理模型输出（CTC解码）
        Args:
            preds: 模型原始输出
        Returns:
            识别出的文本字符串
        """
        try:
            # 应用softmax获取概率
            outprobs = F.softmax(torch.tensor(preds), dim=-1)
            preds_idx = torch.argmax(outprobs, -1).cpu().numpy()

            if self.label_mapping and len(preds_idx.shape) == 2:
                # CTC解码：去除重复和空白标签
                batch_size, length = preds_idx.shape
                results = []

                for i in range(batch_size):
                    pred_idx = preds_idx[i].tolist()
                    last_p = 0
                    str_pred = []

                    for p in pred_idx:
                        if p != last_p and p != 0:  # 去除重复和空白
                            if p in self.label_mapping:
                                str_pred.append(self.label_mapping[p])
                        last_p = p

                    results.append(''.join(str_pred))

                return results[0] if results else ""

        except Exception as e:
            logger.error(f"后处理失败: {e}")

        return ""

    def recognize_base64(self, base64_str: str, calculate: bool = False) -> Dict[str, Any]:
        """
        识别base64格式的图片，可选计算数学表达式
        Args:
            base64_str: base64编码的图片数据
            calculate: 是否计算数学表达式结果
        Returns:
            包含识别结果和状态的字典
        """
        start_time = time.time()
        self.request_count += 1
        request_id = f"req_{self.request_count:06d}"

        try:
            logger.info(f"[{request_id}] 开始处理识别请求, calculate={calculate}")

            # 1. base64解码
            image = self.base64_to_image(base64_str)
            logger.debug(f"[{request_id}] Base64解码完成，图像尺寸: {image.shape}")

            # 2. 预处理
            input_data = self.preprocess(image)
            logger.debug(f"[{request_id}] 图像预处理完成")

            # 3. 模型推理
            preds = self.sess.run([self.output_name], {self.input_name: input_data})
            logger.debug(f"[{request_id}] 模型推理完成")

            # 4. 后处理
            result_text = self.postprocess(preds[0])
            processing_time = time.time() - start_time

            # 5. 可选计算
            calculation_result = None
            calculation_success = False

            if calculate and config.ENABLE_CALCULATION:
                calculation_result = calculator.calculate_from_text(result_text)
                calculation_success = calculation_result is not None
                logger.debug(f"[{request_id}] 计算完成: {result_text} = {calculation_result}")

            logger.info(f"[{request_id}] 识别完成: '{result_text}', 耗时: {processing_time:.3f}s")

            response = {
                "success": True,
                "text": result_text,
                "processing_time": round(processing_time, 3),
                "request_id": request_id,
                "error": None
            }

            # 添加计算结果
            if calculate:
                response["calculation"] = {
                    "success": calculation_success,
                    "result": calculation_result,
                    "expression": result_text
                }
                # 如果要求计算但计算失败，整个请求标记为失败
                if not calculation_success:
                    response["success"] = False
                    response["error"] = "表达式计算失败"

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"识别过程出错: {str(e)}"
            logger.error(f"[{request_id}] {error_msg}")

            response = {
                "success": False,
                "text": "",
                "processing_time": round(processing_time, 3),
                "request_id": request_id,
                "error": error_msg
            }

            if calculate:
                response["calculation"] = {
                    "success": False,
                    "result": None,
                    "expression": ""
                }

            return response


# 全局服务实例
_ocr_service = None


def get_ocr_service():
    """获取全局OCR服务实例"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService.get_instance()
    return _ocr_service
