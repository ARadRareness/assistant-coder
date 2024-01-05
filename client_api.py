import requests
import uuid

BASE_URL = (
    "http://127.0.0.1:17173"  # Change this URL according to your server configuration
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
    conversation_id: str, user_message: str, single_message_mode: bool = False
):
    payload = {
        "conversation_id": conversation_id,
        "message": user_message,
        "single_message_mode": single_message_mode == True,
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
    # Example usage:
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
