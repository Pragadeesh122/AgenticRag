import json
import logging
from clients import openai_client
from tools import tools
from functions.tool_router import execute_tool_call

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
logger = logging.getLogger("orchestrator")


def main():
    print("Hello from agenticrag!")
    messages = [{"role": "system", "content": "Always answer in humor"}]

    while True:
        content = input("")

        if content == "exit":
            print(messages)
            with open("results.json", "w") as file:
                json.dump(messages, file, indent=2)
            break

        messages.append({"role": "user", "content": content})
        while True:
            response = openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=messages,
                tools=tools,
            )

            message = response.choices[0].message
            logger.info(f"tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out")

            if not message.tool_calls:
                logger.info("response: text")
                print(message.content)
                break

            logger.info(f"tool_calls: {[t.function.name for t in message.tool_calls]}")
            messages.append(message.model_dump())
            for tool_call in message.tool_calls:
                messages.append(execute_tool_call(tool_call))

        messages.append({"role": "assistant", "content": message.content})
        print("----" * 30)


if __name__ == "__main__":
    main()
