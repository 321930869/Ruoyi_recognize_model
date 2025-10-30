import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger('Calculator')


class ExpressionCalculator:
    """数学表达式计算器（专门处理若依验证码格式）"""

    # 支持的运算符映射
    OPERATOR_MAP = {
        '×': '*',
        '÷': '/',
        '*': '*',
        '/': '/',
        '+': '+',
        '-': '-'
    }

    @staticmethod
    def extract_expression(text: str) -> Optional[Tuple[str, str, str]]:
        """
        从识别文本中提取数学表达式
        格式如: '4 * 0=?' -> ('4', '*', '0')
        Returns: (数字1, 运算符, 数字2) 或 None
        """
        if not text or '=?' not in text:
            return None

        # 提取等号前的部分
        expression_part = text.split('=?')[0].strip()

        # 匹配模式: 数字 运算符 数字
        # 支持多种运算符表示法
        pattern = r'(\d+)\s*([×÷*/+\-])\s*(\d+)'
        match = re.search(pattern, expression_part)

        if not match:
            logger.warning(f"无法解析表达式: {text}")
            return None

        num1, operator, num2 = match.groups()

        # 标准化运算符
        operator = ExpressionCalculator.OPERATOR_MAP.get(operator, operator)

        return num1, operator, num2

    @staticmethod
    def safe_calculate(num1: str, operator: str, num2: str) -> Optional[int]:
        """
        安全计算数学表达式
        Returns: 计算结果 或 None（计算失败时）
        """
        try:
            n1, n2 = int(num1), int(num2)

            if operator == '+':
                return n1 + n2
            elif operator == '-':
                return n1 - n2
            elif operator == '*':
                return n1 * n2
            elif operator == '/':
                if n2 == 0:
                    logger.warning("除零错误")
                    return None
                return n1 // n2  # 整数除法
            else:
                logger.warning(f"不支持的运算符: {operator}")
                return None

        except (ValueError, TypeError) as e:
            logger.error(f"数值转换错误: {e}")
            return None
        except Exception as e:
            logger.error(f"计算错误: {e}")
            return None

    @classmethod
    def calculate_from_text(cls, text: str) -> Optional[int]:
        """
        从识别文本计算数学表达式结果
        Returns: 计算结果 或 None（计算失败时）
        """
        expression = cls.extract_expression(text)
        if not expression:
            return None

        num1, operator, num2 = expression
        return cls.safe_calculate(num1, operator, num2)


# 全局计算器实例
calculator = ExpressionCalculator()
