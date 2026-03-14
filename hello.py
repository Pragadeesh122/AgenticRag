import json
from client import client
from tool_definitions import tools
from functions import search
import os


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
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=messages,
                tools=tools,
            )

            message = response.choices[0].message

            if not message.tool_calls:
                print(message.content)
                break

            messages.append(message.model_dump())
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = search(**args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

        messages.append({"role": "assistant", "content": message.content})
        print("----" * 30)


if __name__ == "__main__":
    main()
