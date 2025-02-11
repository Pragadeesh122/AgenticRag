
import asyncio
from ollama import AsyncClient


messages = []

async def main():
    prompt= input("Ask your questions! Ready to help :")

    if prompt == "exit":
        return "exit"
        

    messages.append({"role":"user", "content": f"{prompt}" })
    response = await AsyncClient().chat(model='qwen2.5', messages = messages,stream=True)

    full_response = ""
    async for chunk in response:
        full_response+=chunk.message.content
        print(chunk.message.content, end="", flush=True)
 
    messages.append({"role": "assistant", "content" : full_response})
    print(end="\n\n")


while True:
    value = asyncio.run(main())
    if value == "exit":
        break


