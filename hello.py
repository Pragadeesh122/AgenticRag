import requests
from google.genai import types
from client import client


def main():
    print("Hello from agenticrag!")

    respone = client.models.generate_content(model="gemini-3-flash-preview",contents="Hey there")

    print(respone.text)




if __name__ == "__main__":
    main()
