"""大模型统一客户端：把 LLM 封装成"会写字的函数"。

对外只暴露 LLMClient.chat(prompt, system) -> str；
所有 AI 页面（JD 生成、制度问答、数据点评）都复用这一个入口，
便于统一处理超时、失败兜底与后续限流。
"""
from django.conf import settings
from openai import OpenAI


class LLMError(Exception):
    """大模型调用失败的统一异常，由视图层捕获并转成友好提示。"""


class LLMClient:
    """懒加载单例客户端，避免每次请求都重复初始化。"""

    _client = None

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            if not settings.AI_API_KEY:
                # 没配环境变量：直接给出明确原因，而不是报一堆底层堆栈
                raise LLMError('未配置 AI_API_KEY 环境变量，请先设置大模型 API Key')
            cls._client = OpenAI(
                api_key=settings.AI_API_KEY,
                base_url=settings.AI_BASE_URL,
                timeout=settings.AI_TIMEOUT,  # T6：超时控制，防止页面卡死
            )
        return cls._client

    @classmethod
    def chat(cls, prompt, system=None):
        """发送提示词，返回模型生成的文本。

        :param prompt:  用户问题 / 任务（必填）
        :param system:  系统角色设定（可选），给模型定"人设"
        :return:        模型返回的纯文本
        :raises LLMError: 调用失败时抛出，由视图兜底，不让页面崩溃
        """
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})

        try:
            resp = cls._get_client().chat.completions.create(
                model=settings.AI_MODEL,
                messages=messages,
                temperature=0.7,  # 随机度：越低越稳定，越高越发散
            )
            return (resp.choices[0].message.content or '').strip()
        except LLMError:
            raise
        except Exception as e:  # 网络错误 / Key 无效 / 模型名错误等
            raise LLMError(f'大模型调用失败：{e}') from e
