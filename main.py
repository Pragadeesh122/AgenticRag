import json
import logging
from clients import openai_client
from tools import tools
from functions.tool_router import execute_tool_call
from utils.summarizer import summarize_messages

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
logger = logging.getLogger("orchestrator")

MAX_PROMPT_TOKENS = 5000
MAX_TOOL_CALLS = 3


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
        tool_call_count = 0
        try:
            while True:
                response = openai_client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=messages,
                    tools=tools,
                )

                message = response.choices[0].message
                logger.info(
                    f"tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out"
                )

                if not message.tool_calls or tool_call_count >= MAX_TOOL_CALLS:
                    if tool_call_count >= MAX_TOOL_CALLS:
                        logger.info(f"max tool calls reached ({MAX_TOOL_CALLS})")
                        response = openai_client.chat.completions.create(
                            model="gpt-5-mini",
                            messages=messages,
                        )
                        message = response.choices[0].message
                        logger.info(
                            f"tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out"
                        )
                    logger.info("response: text")
                    print(message.content)
                    break

                tool_call_count += 1
                logger.info(
                    f"tool_calls: {[t.function.name for t in message.tool_calls]} ({tool_call_count}/{MAX_TOOL_CALLS})"
                )
                messages.append(message.model_dump())
                for tool_call in message.tool_calls:
                    messages.append(execute_tool_call(tool_call))
        except KeyboardInterrupt:
            print("\nInterrupted.")
            break
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            print(f"Something went wrong: {e}")
            messages.pop()  # remove the failed user message
            continue

        messages.append({"role": "assistant", "content": message.content})

        if response.usage.prompt_tokens > MAX_PROMPT_TOKENS:
            messages = summarize_messages(messages)

        print("----" * 30)


if __name__ == "__main__":
    main()
