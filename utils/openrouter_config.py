import os
import time

import backoff
from google import genai

from utils.my_logging import get_logger

_log = get_logger(__name__)


# 状态图标
SUCCESS_ICON = "✓"
ERROR_ICON = "✗"
WAIT_ICON = "⟳"


# 验证环境变量
api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL")

if not api_key:
    _log.error(f"{ERROR_ICON} 未找到 GEMINI_API_KEY 环境变量")
    raise ValueError("GEMINI_API_KEY not found in environment variables")
if not model:
    model = "gemini-1.5-flash"
    _log.info(f"{WAIT_ICON} 使用默认模型: {model}")

# 初始化 Gemini 客户端
client = genai.Client(api_key=api_key)
_log.info(f"{SUCCESS_ICON} Gemini 客户端初始化成功")


@backoff.on_exception(
    backoff.expo, (Exception), max_tries=5, max_time=300, giveup=lambda e: "AFC is enabled" not in str(e)
)
def generate_content_with_retry(model, contents, config=None):
    """带重试机制的内容生成函数"""
    try:
        _log.info(f"{WAIT_ICON} 正在调用 Gemini API...")
        _log.info(f"请求内容: {contents[:500]}..." if len(str(contents)) > 500 else f"请求内容: {contents}")
        _log.info(f"请求配置: {config}")

        response = client.models.generate_content(model=model, contents=contents, config=config)

        _log.info(f"{SUCCESS_ICON} API 调用成功")
        _log.info(
            f"响应内容: {response.text[:500]}..." if len(str(response.text)) > 500 else f"响应内容: {response.text}"
        )
        return response
    except Exception as e:
        if "AFC is enabled" in str(e):
            _log.warning(f"{ERROR_ICON} 触发 API 限制，等待重试... 错误: {str(e)}")
            time.sleep(5)
            raise

        _log.exception(f"{ERROR_ICON} API 调用失败: ", e)
        raise


def get_chat_completion(messages, model=None, max_retries=3, initial_retry_delay=1):
    """获取聊天完成结果，包含重试逻辑"""
    try:
        if model is None:
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        _log.info(f"{WAIT_ICON} 使用模型: {model}")
        _log.debug(f"消息内容: {messages}")

        for attempt in range(max_retries):
            try:
                # 转换消息格式
                prompt = ""
                system_instruction = None

                for message in messages:
                    role = message["role"]
                    content = message["content"]
                    if role == "system":
                        system_instruction = content
                    elif role == "user":
                        prompt += f"User: {content}\n"
                    elif role == "assistant":
                        prompt += f"Assistant: {content}\n"

                # 准备配置
                config = {"response_mime_type": "application/json"}
                if system_instruction:
                    config["system_instruction"] = system_instruction

                # 调用 API
                response = generate_content_with_retry(model=model, contents=prompt.strip(), config=config)

                if response is None:
                    _log.warning(f"{ERROR_ICON} 尝试 {attempt + 1}/{max_retries}: API 返回空值")
                    if attempt < max_retries - 1:
                        retry_delay = initial_retry_delay * (2**attempt)
                        _log.info(f"{WAIT_ICON} 等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    return None

                _log.debug(f"API 原始响应: {response.text}")
                _log.info(f"{SUCCESS_ICON} 成功获取响应")
                return response.text

            except Exception as e:
                _log.exception(f"{ERROR_ICON} 尝试 {attempt + 1}/{max_retries} 失败: ", e)
                if attempt < max_retries - 1:
                    retry_delay = initial_retry_delay * (2**attempt)
                    _log.info(f"{WAIT_ICON} 等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    _log.exception(f"{ERROR_ICON} 最终错误: ", e)
                    return None

    except Exception as e:
        _log.exception(f"{ERROR_ICON} get_chat_completion 发生错误: ", e)
        return None
