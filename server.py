import datetime
import os
import sys
import shutil
import traceback
import struct
from typing import Dict, List, Optional
from flask import Flask, Response, jsonify, request, send_file  # type: ignore
import uuid
import hashlib

from faster_whisper import WhisperModel  # type: ignore

from language_models.memory_manager import MemoryManager
from language_models.tool_manager import ToolManager

from language_models.model_conversation import ModelConversation
from language_models.model_manager import ModelManager
from language_models.model_message import MessageMetadata
from language_models.audio.text_to_speech_engine import TextToSpeechEngine

from language_models.model_state import ModelState

from dotenv import load_dotenv

if not os.path.exists(".env"):
    shutil.copy(".env_defaults", ".env")

load_dotenv()

app = Flask(__name__)

conversations: Dict[str, ModelConversation] = {}

memory_manager: MemoryManager = MemoryManager()

text_to_speech_engine: Optional[TextToSpeechEngine] = None

# Global variable for WhisperModel
whisper_model = None


@app.route("/start_new_conversation", methods=["GET"])
def start_conversation() -> Response:
    conversation_id = str(uuid.uuid4())
    with ModelState.get_lock():
        active_model = ModelState.get_active_model()
        if not active_model:
            raise ValueError("No model is available right now.")

    conversations[conversation_id] = ModelConversation(
        memory_manager, active_model.get_model_path()
    )
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

        model_path = conversations[conversation_id].get_model_path()

        return jsonify({"result": True, "info": {"path": model_path}})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/change_model", methods=["POST"])
def change_model() -> Response:
    try:
        data = request.get_json()
        model_name = data.get("model_name")
        conversation_id = data.get("conversation_id")

        if not conversation_id:
            raise ValueError("Missing conversation_id parameter in the request.")

        if conversation_id not in conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found.")

        if not model_name:
            raise ValueError("Missing model_name in the request.")

        with ModelState.get_lock():
            model_manager = ModelState.get_model_manager()

            if not model_manager:
                raise ValueError("No model manager found.")

            available_models = model_manager.get_available_models()
            if model_name not in available_models:
                raise ValueError(f"Model {model_name} not found.")

            conversation = conversations[conversation_id]
            conversation.set_model_path(model_name)
        return jsonify({"result": True})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/get_available_models", methods=["GET"])
def get_available_models() -> Response:
    try:
        with ModelState.get_lock():
            model_manager = ModelState.get_model_manager()

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

        with ModelState.get_lock():
            model_manager = ModelState.get_model_manager()

            if not model_manager:
                raise ValueError("No model manager found.")

            model_path = conversations[conversation_id].get_model_path()
            model_manager.change_model(model_path)

            response = conversations[conversation_id].generate_message(
                model_manager.active_models[0],
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
                        suggestions = conversations[
                            conversation_id
                        ].generate_suggestions(model_manager.active_models[0])
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


@app.route("/stt", methods=["POST"])
def stt():
    global whisper_model  # Use the global variable
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        # Generate a unique filename using MD5 hash
        content = file.read()
        md5_hash = hashlib.md5(content).hexdigest()
        filename = f"{md5_hash}.wav"
        filepath = os.path.join("output", filename)

        # Save the file temporarily
        with open(filepath, "wb") as audio_file:
            audio_file.write(content)

        # Initialize Whisper model if it hasn't been already
        if whisper_model is None:
            whisper_model = WhisperModel(
                "large-v2", device="cuda", compute_type="float16"
            )

        initial_whisper_prompt = "DEFAULT"
        language = "en"

        # Transcribe audio
        segments, _info = whisper_model.transcribe(  # type: ignore
            filepath,
            beam_size=5,
            initial_prompt=initial_whisper_prompt,
            language=language,
            vad_filter=True,
            # word_timestamps=True,
        )
        transcript = " ".join([x.text for x in segments])

        # Clean up the saved file
        os.remove(filepath)

        return jsonify({"result": True, "transcript": transcript})

    return jsonify({"result": False, "error_message": ""})


def allowed_file(filename: Optional[str]) -> bool:
    if filename:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ["wav"]
    else:
        return False


@app.route("/code_interpreter", methods=["POST"])
def code_interpreter() -> Response:
    try:
        data = request.get_json()
        conversation_id = data.get("conversation_id")
        user_message = data.get("message")
        ask_permission_to_run_tools = data.get("ask_permission_to_run_tools")

        if not conversation_id or not user_message:
            raise ValueError("Missing conversation_id or message in the request.")

        if conversation_id not in conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found.")

        code_interpreter = ToolManager().get_target_tool({"tool": "code_interpreter"})

        response: str = ""

        if code_interpreter:
            metadata = MessageMetadata(
                datetime.datetime.now(), [], ask_permission_to_run_tools, ""
            )

            with ModelState.get_lock():
                model_manager = ModelState.get_model_manager()

                if not model_manager:
                    raise ValueError("No model manager found.")

                model_path = conversations[conversation_id].get_model_path()
                model_manager.change_model(model_path)

                response = code_interpreter.action(
                    {},
                    model_manager.active_models[0],
                    conversations[conversation_id].get_messages(),
                    metadata,
                )
                print(response)

        return jsonify({"result": True, "response": response})
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


mock_llama = False

if __name__ == "__main__":
    # load_model_manager(mock_llama)

    if mock_llama:
        print("WARNING: Mock Mode")
    else:
        llama_cpp_path = os.getenv("LLAMA_CPP_PATH", "bin")
        model_manager = _get_model_manager(llama_cpp_path, mock_llama)

        if not model_manager:
            print("Error: Model manager not found.")
            sys.exit(-1)
        else:
            ModelState.initialize(model_manager)

        with ModelState.get_lock():
            model_manager.load_model()

        import atexit

        # Increase the likelihood that the model manager is cleaned up properly
        atexit.register(model_manager.__del__)

    app.run(debug=False, port=17173)
