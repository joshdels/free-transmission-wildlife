import os
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.environ["ANTROPIC_API_KEY"])


async def ask_ai(message: str) -> str:

    response = await client.messages.create(
        model="claude-sonnect-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
    )

    return response.content[0].text
