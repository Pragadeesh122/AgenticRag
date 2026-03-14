import json
from clients import openai_client
from tools import tools
from functions.tool_router import execute_tool_call


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

            if not message.tool_calls:
                print(message.content)
                break

            messages.append(message.model_dump())
            for tool_call in message.tool_calls:
                messages.append(execute_tool_call(tool_call))

        messages.append({"role": "assistant", "content": message.content})
        print("----" * 30)


if __name__ == "__main__":
    main()
