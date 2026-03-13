import requests
from google.genai import types
from client import client


def main():
    print("Hello from agenticrag!")
    messages = []
    messages.append(types.Content(role="system",parts=[types.Part(text="Always answer in humor")]))
    while True:
        content = input("")
        
        if content == "exit":
            print(messages)
            break

        messages.append(types.Content(role="user", parts=[types.Part(text=content)]))
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=messages,
        )
        messages.append(types.Content(role="model", parts=[types.Part(text=response.text)]))
        print(response.text)
        print("----"*80)






if __name__ == "__main__":

    main()
