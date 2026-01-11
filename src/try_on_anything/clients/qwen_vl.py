from openai import AsyncOpenAI
import os
from pydantic import BaseModel
from typing import Optional, Union, AsyncGenerator, Dict, Literal, List, Any


class ChatResponse(BaseModel):
    """聊天响应结构，包含思考内容和最终回复"""
    content: str
    reasoning_content: Optional[str] = None


class ChatChunkDelta(BaseModel):
    """聊天流式输出的增量结构，可以为思考内容或正常回复内容"""
    type: Literal['reasoning', 'content']  # 'reasoning' 或 'content'
    content: str


class QwenVLClient:
    """ Qwen-VL 客户端封装，用于与 OpenAI 兼容的接口进行交互

    Args:
        api_key (str, optional): API 密钥，如果不提供则从环境变量 DASHSCOPE_API_KEY 读取，默认值为 None。
        base_url (str, optional): API 基础 URL，默认值为 "https://dashscope.aliyuncs.com/compatible-mode/v1"。
    """

    def __init__(
            self,
            api_key: Optional[str] = None,
            base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ):

        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key 未提供，请设置 DASHSCOPE_API_KEY 环境变量或传入 api_key 参数")
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=base_url)

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str = "qwen3-vl-plus",
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        enable_thinking: bool = False,
        thinking_budget: Optional[int] = None
    ) -> Union[ChatResponse, AsyncGenerator[dict, None]]:
        """与 Qwen-VL 模型进行对话

        Args:
            messages: 消息列表，格式与 OpenAI API 兼容
            model: 模型名称，默认为 "qwen-vl-plus"
            stream: 是否使用流式输出，默认为 False
            temperature: 温度参数，控制输出随机性
            max_tokens: 最大输出 token 数
            enable_thinking: 是否启用思考模式，默认为 False
            thinking_budget: 思考预算，单位为 token

        Returns:
            非流式模式返回 ChatResponse，流式模式返回异步生成器（yield dict 包含 content 或 reasoning_content）
        """
        kwargs = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        if enable_thinking and thinking_budget is None:
            raise ValueError("启用思考模式时，必须提供 thinking_budget 参数")
        elif enable_thinking and thinking_budget <= 0:
            raise ValueError("thinking_budget 参数必须为正整数")

        if enable_thinking:
            kwargs["extra_body"] = {
                "enable_thinking":
                True,
                "thinking_budget":
                thinking_budget if thinking_budget is not None else 8192
            }

        if stream:
            return self._stream_chat(**kwargs)
        else:
            response = await self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            reasoning_content = getattr(message, 'reasoning_content', None)
            return ChatResponse(content=message.content or "",
                                reasoning_content=reasoning_content)

    async def _stream_chat(self, **kwargs) -> AsyncGenerator[Dict, None]:
        """流式输出的内部实现

        Yields:
            ChatChunkDelta: 包含思考内容或最终回复内容的增量数据类
        """
        response = await self.client.chat.completions.create(**kwargs)
        async for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # 处理思考内容
            reasoning = getattr(delta, 'reasoning_content', None)
            if reasoning:
                yield ChatChunkDelta(type='reasoning', content=reasoning)
            # 处理最终回复内容
            if delta.content:
                yield ChatChunkDelta(type='content', content=delta.content)
