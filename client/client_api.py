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
        use_suggestions: bool = False,
    ):
        self.conversation_id = start_conversation()
        self.single_message_mode = single_message_mode
        self.use_tools = use_tools
        self.use_reflections = use_reflections
        self.use_suggestions = use_suggestions

    def add_system_message(self, message: str):
        return add_system_message(self.conversation_id, message)

    def add_user_message(self, message: str):
        return add_user_message(self.conversation_id, message)

    def add_assistant_message(self, message: str):
        return add_assistant_message(self.conversation_id, message)

    def get_conversation(self):
        return get_conversation(self.conversation_id)

    def get_model_info(self):
        return get_model_info(self.conversation_id)

    def get_available_models(self):
        return get_available_models()

    def change_model(self, model_name: str):
        return change_model(model_name)

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
            use_suggestions=self.use_suggestions,
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


def add_user_message(conversation_id: str, message: str):
    payload = {"conversation_id": conversation_id, "message": message}
    response = requests.post(f"{BASE_URL}/add_user_message", json=payload)

    if response.status_code != 200:
        print(f"Error adding user message. status_code={response.status_code}")
        return False

    data = response.json()

    return data["result"]


def add_assistant_message(conversation_id: str, message: str):
    payload = {"conversation_id": conversation_id, "message": message}
    response = requests.post(f"{BASE_URL}/add_assistant_message", json=payload)

    if response.status_code != 200:
        print(f"Error adding assistant message. status_code={response.status_code}")
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


def get_available_models():
    response = requests.get(f"{BASE_URL}/get_available_models")
    if response.status_code != 200:
        print(f"Error getting available models. status_code={response.status_code}")
        return []

    data = response.json()

    if data["result"]:
        return data["models"]
    else:
        print(f"Error getting available models: {data}")
        return []


def change_model(model_name: str):
    payload = {"model_name": model_name}
    response = requests.post(f"{BASE_URL}/change_model", json=payload)

    if response.status_code != 200:
        print(f"Error changing model. status_code={response.status_code}")
        return False

    data = response.json()

    return data["result"]


def generate_response(
    conversation_id: str,
    user_message: str,
    selected_files: List[str] = [],
    max_tokens: int = 200,
    temperature: float = 0.2,
    single_message_mode: bool = False,
    use_tools: bool = False,
    use_reflections: bool = False,
    use_suggestions: bool = False,
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
        "use_suggestions": use_suggestions == True,
    }

    response = requests.post(f"{BASE_URL}/generate_response", json=payload)

    if response.status_code != 200:
        print(f"Error generating response. status_code={response.status_code}")
        return None

    data = response.json()

    if data["result"]:
        if use_suggestions:
            return data["response"], data["suggestions"]
        else:
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
