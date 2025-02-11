
import asyncio
from ollama import AsyncClient


async def main():
    response = await AsyncClient().generate(model='llama3.2', prompt="Whats the weather in mars", system="Answer in a sarcastic way",stream=True)

    async for chunk in response:
        print(chunk.response, end="", flush=True)

asyncio.run(main())


