import datetime
import os
import sys
import traceback
import yaml
import struct
from typing import Dict, List, Optional
from flask import Flask, Response, jsonify, request, send_file  # type: ignore
import uuid
from language_models.memory_manager import MemoryManager

from language_models.model_conversation import ModelConversation
from language_models.model_manager import ModelManager
from language_models.model_message import MessageMetadata
from language_models.audio.text_to_speech_engine import TextToSpeechEngine

app = Flask(__name__)

conversations: Dict[str, ModelConversation] = {}

model_manager: Optional[ModelManager] = None
memory_manager: MemoryManager = MemoryManager()

text_to_speech_engine: Optional[TextToSpeechEngine] = None


@app.route("/start_new_conversation", methods=["GET"])
def start_conversation() -> Response:
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = ModelConversation(memory_manager)
    return jsonify({"conversation_id": conversation_id})


@app.route("/add_system_message", methods=["POST"])
def add_system_message() -> Response:
    try:
        data = request.get_json()
        conversation_id = data.get("conversation_id")
        message = data.get("message")

        if not conversation_id or not message:
            raise ValueError("Missing conversation_id or message in the request.")

        if conversation_id not in conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found.")

        timestamp = datetime.datetime.now()
        selected_files = data.get("selected_files")

        metadata = MessageMetadata(timestamp, selected_files)

        conversations[conversation_id].add_system_message(message, metadata)

        return jsonify({"result": True})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/add_user_message", methods=["POST"])
def add_user_message() -> Response:
    try:
        data = request.get_json()
        conversation_id = data.get("conversation_id")
        message = data.get("message")

        if not conversation_id or not message:
            raise ValueError("Missing conversation_id or message in the request.")

        if conversation_id not in conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found.")

        timestamp = datetime.datetime.now()
        selected_files = data.get("selected_files")

        metadata = MessageMetadata(timestamp, selected_files)

        conversations[conversation_id].add_user_message(message, metadata)

        return jsonify({"result": True})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/add_assistant_message", methods=["POST"])
def add_assistant_message() -> Response:
    try:
        data = request.get_json()
        conversation_id = data.get("conversation_id")
        message = data.get("message")

        if not conversation_id or not message:
            raise ValueError("Missing conversation_id or message in the request.")

        if conversation_id not in conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found.")

        timestamp = datetime.datetime.now()
        selected_files = data.get("selected_files")

        metadata = MessageMetadata(timestamp, selected_files)

        conversations[conversation_id].add_assistant_message(message, metadata)

        return jsonify({"result": True})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/get_conversation", methods=["GET"])
def get_conversation() -> Response:
    try:
        conversation_id = request.args.get("conversation_id")

        if not conversation_id:
            raise ValueError("Missing conversation_id parameter in the request.")

        if conversation_id not in conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found.")

        conversation_data: List[Dict[str, str]] = [
            {"role": message.get_role(), "message": message.get_content()}
            for message in conversations[conversation_id].get_messages()
        ]

        return jsonify({"result": True, "conversation": conversation_data})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error": str(e)})


@app.route("/get_model_info", methods=["GET"])
def get_model_info() -> Response:
    try:
        conversation_id = request.args.get("conversation_id")

        if not conversation_id:
            raise ValueError("Missing conversation_id parameter in the request.")

        if conversation_id not in conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found.")

        if model_manager:
            model_path = model_manager.models[0].model_path
        else:
            model_path = "MOCK_PATH"

        return jsonify({"result": True, "info": {"path": model_path}})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/change_model", methods=["POST"])
def change_model() -> Response:
    try:
        data = request.get_json()
        model_name = data.get("model_name")

        if not model_name:
            raise ValueError("Missing model_name in the request.")

        if not model_manager:
            raise ValueError("No model manager found.")

        model_manager.change_model(model_name)
        return jsonify({"result": True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/get_available_models", methods=["GET"])
def get_available_models() -> Response:
    try:
        if model_manager:
            return jsonify(
                {"result": True, "models": model_manager.get_available_models()}
            )
        else:
            return jsonify(
                {"result": False, "error_message": "No model manager found."}
            )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/generate_response", methods=["POST"])
def generate_response() -> Response:
    try:
        data = request.get_json()
        conversation_id = data.get("conversation_id")
        user_message = data.get("message")
        max_tokens = data.get("max_tokens")
        single_message_mode = data.get("single_message_mode")
        use_tools = data.get("use_tools")
        use_reflections = data.get("use_reflections")
        use_suggestions = data.get("use_suggestions")
        use_knowledge = data.get("use_knowledge")
        ask_permission_to_run_tools = data.get("ask_permission_to_run_tools")
        clipboard_content = data.get("clipboard_content")

        timestamp = datetime.datetime.now()
        selected_files = data.get("selected_files")

        metadata = MessageMetadata(
            timestamp, selected_files, ask_permission_to_run_tools, clipboard_content
        )

        if not conversation_id or not user_message:
            raise ValueError("Missing conversation_id or message in the request.")

        if conversation_id not in conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found.")

        conversations[conversation_id].add_user_message(user_message, metadata)

        if not model_manager:
            raise ValueError("No model manager found.")

        response = conversations[conversation_id].generate_message(
            model_manager.models[0],
            max_tokens,
            single_message_mode,
            use_metadata=True,
            use_tools=use_tools,
            use_reflections=use_reflections,
            use_knowledge=use_knowledge,
            ask_permission_to_run_tools=ask_permission_to_run_tools,
        )

        if use_suggestions:
            suggestions = []
            for _ in range(2):
                try:
                    suggestions = conversations[conversation_id].generate_suggestions(
                        model_manager.models[0]
                    )
                    break
                except Exception as e:
                    print(e)
                    suggestions = []

            return jsonify(
                {"result": True, "response": response, "suggestions": suggestions}
            )
        else:
            return jsonify({"result": True, "response": response})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error": str(e)})


@app.route("/tts", methods=["POST"])
def tts() -> Response:
    global text_to_speech_engine
    try:
        data = request.get_json()
        text = data.get("text")

        if not text:
            raise ValueError("Missing 'text' in the request.")

        if not text_to_speech_engine:
            text_to_speech_engine = TextToSpeechEngine()

        wav_file_paths = text_to_speech_engine.text_to_speech_with_split(text)

        def generate():
            for wav_file_path in wav_file_paths:
                with open(wav_file_path, "rb") as wav_file:
                    wav_data = wav_file.read()
                    # Prefix each WAV file with its size using a 4-byte integer
                    yield struct.pack("<I", len(wav_data))
                    yield wav_data

        return Response(generate(), mimetype="audio/wav")

    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


def _get_model_manager(llama_cpp_path: str, mock_llama: bool = False):
    if mock_llama:
        print("WARNING: Mock Mode")
    else:
        if os.name == "nt":
            binary_path = os.path.join(llama_cpp_path, "server.exe")
        else:
            binary_path = os.path.join(llama_cpp_path, "server")

        if not os.path.exists(binary_path):
            print(
                "Error:",
                f"Add the llama.cpp server binary and (for Windows) llama.dll into the {llama_cpp_path} folder. See https://github.com/ggerganov/llama.cpp.",
            )
            sys.exit(-1)

        gguf_models = list(filter(lambda f: f.endswith(".gguf"), os.listdir("models")))

        model_manager = ModelManager(binary_path, 8000)

        if len(model_manager.get_available_models()) == 0:
            if not gguf_models:
                print("Error: Add one or more gguf models to the models folder.")
                sys.exit(-1)

        return model_manager


def read_config() -> Dict[str, str]:
    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)

            if config:
                return config
    return {}


mock_llama = False

if __name__ == "__main__":
    # load_model_manager(mock_llama)

    if mock_llama:
        print("WARNING: Mock Mode")
    else:

        config = read_config()
        llama_cpp_path = config.get("llama_cpp_path", "bin")
        model_manager = _get_model_manager(llama_cpp_path, mock_llama)

        if not model_manager:
            print("Error: Model manager not found.")
            sys.exit(-1)

        model_manager.load_model()

        import atexit

        # Increase the likelihood that the model manager is cleaned up properly
        atexit.register(model_manager.__del__)

    app.run(debug=False, port=17173)
