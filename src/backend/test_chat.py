import asyncio
import httpx


async def test_chat():
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8000/api/v1/chat",
            json={
                "messages": [
                    {"role": "user", "content": "你好，请自我介绍"}
                ]
            },
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")


if __name__ == "__main__":
    asyncio.run(test_chat())
