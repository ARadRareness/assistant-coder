import requests
import struct
from typing import Any, Dict, Sequence, Tuple

BASE_URL = (
    "http://127.0.0.1:17173"  # Change this URL according to your server configuration
)


class Model:
    def __init__(
        self,
        single_message_mode: bool = True,
        use_tools: bool = False,
        use_reflections: bool = False,
        use_knowledge: bool = False,
        ask_permission_to_run_tools: bool = False,
    ):
        self.conversation_id = start_conversation()
        self.single_message_mode = single_message_mode
        self.use_tools = use_tools
        self.use_reflections = use_reflections
        self.use_knowledge = use_knowledge
        self.ask_permission_to_run_tools = ask_permission_to_run_tools

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
        return change_model(self.conversation_id, model_name)

    def generate_response(
        self,
        message: str,
        selected_files: Sequence[str] = [],
        max_tokens: int = 200,
        temperature: float = 0.2,
        clipboard_content: str = "",
    ) -> str:
        return generate_response(
            self.conversation_id,
            message,
            selected_files=selected_files,
            max_tokens=max_tokens,
            temperature=temperature,
            single_message_mode=self.single_message_mode,
            use_tools=self.use_tools,
            use_reflections=self.use_reflections,
            use_knowledge=self.use_knowledge,
            ask_permission_to_run_tools=self.ask_permission_to_run_tools,
            clipboard_content=clipboard_content,
        )

    def generate_response_with_suggestions(
        self,
        message: str,
        selected_files: Sequence[str] = [],
        max_tokens: int = 200,
        temperature: float = 0.2,
        clipboard_content: str = "",
    ) -> Tuple[str, Sequence[str]]:

        return generate_response_with_suggestions(
            self.conversation_id,
            message,
            selected_files=selected_files,
            max_tokens=max_tokens,
            temperature=temperature,
            single_message_mode=self.single_message_mode,
            use_tools=self.use_tools,
            use_reflections=self.use_reflections,
            use_knowledge=self.use_knowledge,
            ask_permission_to_run_tools=self.ask_permission_to_run_tools,
            clipboard_content=clipboard_content,
        )


def execute_code(
    conversation_id: str, code: str, ask_permission_to_run_tools: bool = False
) -> str:
    payload = {
        "conversation_id": conversation_id,
        "message": code,
        "ask_permission_to_run_tools": ask_permission_to_run_tools,
    }
    response = requests.post(f"{BASE_URL}/code_interpreter", json=payload)

    if response.status_code != 200:
        print(f"Error executing code. status_code={response.status_code}")
        return ""

    data = response.json()

    if data["result"]:
        return data["response"]
    else:
        print(f"Error executing code: {data}")
        return ""


def start_conversation() -> str:
    response = requests.get(f"{BASE_URL}/start_new_conversation")
    if response.status_code == 200:
        data = response.json()
        return data["conversation_id"]
    else:
        print(f"Error starting conversation. status_code={response.status_code}")
        return ""


def add_system_message(conversation_id: str, message: str) -> bool:
    payload = {"conversation_id": conversation_id, "message": message}
    response = requests.post(f"{BASE_URL}/add_system_message", json=payload)

    if response.status_code != 200:
        print(f"Error adding system message. status_code={response.status_code}")
        return False

    data = response.json()

    return data["result"]


def add_user_message(conversation_id: str, message: str) -> bool:
    payload = {"conversation_id": conversation_id, "message": message}
    response = requests.post(f"{BASE_URL}/add_user_message", json=payload)

    if response.status_code != 200:
        print(f"Error adding user message. status_code={response.status_code}")
        return False

    data = response.json()

    return data["result"]


def add_assistant_message(conversation_id: str, message: str) -> bool:
    payload = {"conversation_id": conversation_id, "message": message}
    response = requests.post(f"{BASE_URL}/add_assistant_message", json=payload)

    if response.status_code != 200:
        print(f"Error adding assistant message. status_code={response.status_code}")
        return False

    data = response.json()

    return data["result"]


def get_conversation(conversation_id: str) -> Sequence[Dict[str, Any]]:
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


def get_model_info(conversation_id: str) -> Dict[str, Any]:
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


def get_available_models() -> Sequence[str]:
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


def change_model(conversation_id: str, model_name: str):
    payload = {
        "conversation_id": conversation_id,
        "model_name": model_name,
    }
    response = requests.post(f"{BASE_URL}/change_model", json=payload)

    if response.status_code != 200:
        print(f"Error changing model. status_code={response.status_code}")
        return False

    data = response.json()

    return data["result"]


def generate_tts(text: str):
    payload = {"text": text}
    response = requests.post(f"{BASE_URL}/tts", json=payload, stream=True)

    if response.status_code != 200:
        print(f"Error generating TTS. status_code={response.status_code}")
        yield b""  # Yield an empty byte string to indicate an error condition gracefully

    try:
        while True:
            # Read the size of the next WAV file (4 bytes = 32 bits integer)
            size_data = response.raw.read(4)
            if not size_data:
                break  # No more data, exit the loop

            # Unpack the 4 bytes to an integer (assuming little-endian byte order)
            (size,) = struct.unpack("<I", size_data)

            # Now read the WAV file of the specified size
            wav_data = response.raw.read(size)
            if wav_data:
                yield wav_data
            else:
                break  # In case the data stream is shorter than expected
    except Exception as e:
        print(f"Error reading TTS data: {e}")
        yield b""


def generate_response(
    conversation_id: str,
    user_message: str,
    selected_files: Sequence[str] = [],
    max_tokens: int = 200,
    temperature: float = 0.2,
    single_message_mode: bool = False,
    use_tools: bool = False,
    use_reflections: bool = False,
    use_knowledge: bool = False,
    ask_permission_to_run_tools: bool = False,
    clipboard_content: str = "",
) -> str:
    response = _base_generate_response(
        conversation_id,
        user_message,
        selected_files=selected_files,
        max_tokens=max_tokens,
        temperature=temperature,
        single_message_mode=single_message_mode,
        use_tools=use_tools,
        use_reflections=use_reflections,
        use_suggestions=False,
        use_knowledge=use_knowledge,
        ask_permission_to_run_tools=ask_permission_to_run_tools,
        clipboard_content=clipboard_content,
    )

    if response:
        return response[0]
    else:
        return ""


def generate_response_with_suggestions(
    conversation_id: str,
    user_message: str,
    selected_files: Sequence[str] = [],
    max_tokens: int = 200,
    temperature: float = 0.2,
    single_message_mode: bool = False,
    use_tools: bool = False,
    use_reflections: bool = False,
    use_knowledge: bool = False,
    ask_permission_to_run_tools: bool = False,
    clipboard_content: str = "",
) -> Tuple[str, Sequence[str]]:

    response = _base_generate_response(
        conversation_id,
        user_message,
        selected_files=selected_files,
        max_tokens=max_tokens,
        temperature=temperature,
        single_message_mode=single_message_mode,
        use_tools=use_tools,
        use_reflections=use_reflections,
        use_suggestions=True,
        use_knowledge=use_knowledge,
        ask_permission_to_run_tools=ask_permission_to_run_tools,
        clipboard_content=clipboard_content,
    )

    return response


def transcribe_audio(audio_file_path: str) -> str:
    url = f"{BASE_URL}/stt"
    files = {"file": open(audio_file_path, "rb")}
    response = requests.post(url, files=files)

    if response.status_code != 200:
        print(f"Error transcribing audio. status_code={response.status_code}")
        return ""

    data = response.json()

    if data.get("result"):
        return data.get("transcript", "")
    else:
        print(f"Error transcribing audio: {data.get('error_message')}")
        return ""


def _base_generate_response(
    conversation_id: str,
    user_message: str,
    selected_files: Sequence[str] = [],
    max_tokens: int = 200,
    temperature: float = 0.2,
    single_message_mode: bool = False,
    use_tools: bool = False,
    use_reflections: bool = False,
    use_suggestions: bool = False,
    use_knowledge: bool = False,
    ask_permission_to_run_tools: bool = False,
    clipboard_content: str = "",
) -> Tuple[str, Sequence[str]]:
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
        "use_knowledge": use_knowledge == True,
        "ask_permission_to_run_tools": ask_permission_to_run_tools == True,
        "clipboard_content": clipboard_content,
    }

    response = requests.post(f"{BASE_URL}/generate_response", json=payload)

    if response.status_code != 200:
        print(f"Error generating response. status_code={response.status_code}")
        return "", []

    data = response.json()

    if data["result"]:
        if use_suggestions:
            return data["response"], data["suggestions"]
        else:
            return data["response"], []
    else:
        print(f"Error generating response: {data}")
        return "", []


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

    print(transcribe_audio("wavs\\input_20240321_215405.wav"))
