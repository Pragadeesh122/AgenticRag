import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from clients import openai_client
from tools import tools
from functions.tool_router import execute_tool_call
from utils.summarizer import summarize_messages
from memory import get_user_memory, extract_and_save_memories
from prompts import ORCHESTRATOR

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
logger = logging.getLogger("orchestrator")

MAX_PROMPT_TOKENS = 5000
MAX_TOOL_CALLS = 3


def main():
    print("Hello from agenticrag!")

    # Load semantic memory into system prompt
    system_prompt = ORCHESTRATOR
    user_memory = get_user_memory()
    if user_memory:
        system_prompt += f"\n\nKnown facts about the user:\n{user_memory}"
        logger.info("loaded user memory from Redis")

    messages = [{"role": "system", "content": system_prompt}]

    while True:
        content = input("")

        if content == "exit":
            # Extract and save memories before exiting
            logger.info("extracting memories from conversation")
            extract_and_save_memories(messages)
            with open("results.json", "w") as file:
                json.dump(messages, file, indent=2)
            break

        messages.append({"role": "user", "content": content})
        tool_call_count = 0
        try:
            while True:
                response = openai_client.chat.completions.create(
                    model="gpt-5.4-mini",
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
                        stop_msg = {
                            "role": "system",
                            "content": "You have reached the maximum number of tool calls. Do NOT attempt any more tool calls. Respond with the best answer you can based on the information you have gathered so far.",
                        }
                        messages.append(stop_msg)
                        response = openai_client.chat.completions.create(
                            model="gpt-5-mini",
                            messages=messages,
                        )
                        message = response.choices[0].message
                        messages.remove(stop_msg)
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
                with ThreadPoolExecutor() as executor:
                    futures = {
                        executor.submit(execute_tool_call, tc): tc
                        for tc in message.tool_calls
                    }
                    results = []
                    for future in as_completed(futures):
                        results.append((futures[future], future.result()))
                    # Preserve original tool call order
                    order = {tc.id: i for i, tc in enumerate(message.tool_calls)}
                    results.sort(key=lambda r: order[r[0].id])
                    for _, result in results:
                        messages.append(result)
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
