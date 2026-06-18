import logging
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

logger.info(f"DeepSeek API Key loaded: {settings.deepseek_api_key[:10]}... (len={len(settings.deepseek_api_key)})")

client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com/v1",
)


async def chat_completion(messages: list[dict], model: str = "deepseek-chat", **kwargs):
    try:
        logger.info(f"Sending request to DeepSeek with {len(messages)} messages")
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs,
        )
        logger.info("DeepSeek response received")
        return response.choices[0].message.content
    except Exception as e:
        import traceback
        logger.error(f"DeepSeek API call failed: {e}")
        traceback.print_exc()
        raise RuntimeError(f"LLM API 调用失败: {e}")
