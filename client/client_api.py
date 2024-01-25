import json
import requests
from typing import List

BASE_URL = (
    "http://127.0.0.1:17173"  # Change this URL according to your server configuration
)


class Model:
    def __init__(
        self,
        single_message_mode: bool = True,
        use_tools: bool = False,
        use_reflections: bool = False,
    ):
        self.conversation_id = start_conversation()
        self.single_message_mode = single_message_mode
        self.use_tools = use_tools
        self.use_reflections = use_reflections

    def add_system_message(self, message: str):
        return add_system_message(self.conversation_id, message)

    def get_conversation(self):
        return get_conversation(self.conversation_id)

    def get_model_info(self):
        return get_model_info(self.conversation_id)

    def generate_response(
        self, message: str, selected_files=[], max_tokens=200, temperature=0.2
    ):
        return generate_response(
            self.conversation_id,
            message,
            selected_files=selected_files,
            max_tokens=max_tokens,
            temperature=temperature,
            single_message_mode=self.single_message_mode,
            use_tools=self.use_tools,
            use_reflections=self.use_reflections,
        )


def start_conversation():
    response = requests.get(f"{BASE_URL}/start_new_conversation")
    if response.status_code == 200:
        data = response.json()
        return data["conversation_id"]
    else:
        print(f"Error starting conversation. status_code={response.status_code}")
        return None


def add_system_message(conversation_id: str, message: str):
    payload = {"conversation_id": conversation_id, "message": message}
    response = requests.post(f"{BASE_URL}/add_system_message", json=payload)

    if response.status_code != 200:
        print(f"Error adding system message. status_code={response.status_code}")
        return False

    data = response.json()

    return data["result"]


def get_conversation(conversation_id: str):
    params = {"conversation_id": conversation_id}
    response = requests.get(f"{BASE_URL}/get_conversation", params=params)
    if response.status_code != 200:
        print(f"Error getting conversation. status_code={response.status_code}")
        return []

    data = response.json()

    if data["result"]:
        return data["conversation"]
    else:
        print(f"Error getting conversation: {data}")
        return []


def get_model_info(conversation_id: str):
    params = {"conversation_id": conversation_id}
    response = requests.get(f"{BASE_URL}/get_model_info", params=params)

    if response.status_code != 200:
        print(f"Error getting model info. status_code={response.status_code}")
        return {}

    data = response.json()

    if data["result"]:
        return data["info"]
    else:
        print(f"Error getting model info: {data}")
        return {}


def generate_response(
    conversation_id: str,
    user_message: str,
    selected_files: List[str] = [],
    max_tokens: int = 200,
    temperature: float = 0.2,
    single_message_mode: bool = False,
    use_tools: bool = False,
    use_reflections: bool = False,
):
    payload = {
        "conversation_id": conversation_id,
        "message": user_message,
        "selected_files": selected_files,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "single_message_mode": single_message_mode == True,
        "use_tools": use_tools == True,
        "use_reflections": use_reflections == True,
    }

    response = requests.post(f"{BASE_URL}/generate_response", json=payload)

    if response.status_code != 200:
        print(f"Error generating response. status_code={response.status_code}")
        return None

    data = response.json()

    if data["result"]:
        return data["response"]
    else:
        print(f"Error generating response: {data}")
        return None


if __name__ == "__main__":
    conversation_id = start_conversation()
    if conversation_id:
        model_info = get_model_info(conversation_id)
        prompt = f"You are AC, the helpful AI coding assistant. You are currently running through the following model: {model_info['path']}."
        add_system_message(conversation_id, prompt)

        response = generate_response(
            conversation_id, "The secret code is 1453, remember it."
        )
        response = generate_response(conversation_id, "What is the secret code?")
        response = generate_response(
            conversation_id, "What is the secret code?", single_message_mode=True
        )

        for message in get_conversation(conversation_id):
            print(f"{message['role']}: {message['message']}")
