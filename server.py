import datetime
import os
import sys
from flask import Flask, jsonify, request
import uuid

from language_models.model_conversation import ModelConversation
from language_models.model_manager import ModelManager
from language_models.model_message import MessageMetadata

app = Flask(__name__)

conversations = {}

model_manager = None


@app.route("/start_new_conversation", methods=["GET"])
def start_conversation():
    conversation_id = str(uuid.uuid4())
    conversations[conversation_id] = ModelConversation(single_message_mode=True)
    return jsonify({"conversation_id": conversation_id})


@app.route("/add_system_message", methods=["POST"])
def add_system_message():
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
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/get_conversation", methods=["GET"])
def get_conversation():
    try:
        conversation_id = request.args.get("conversation_id")

        if not conversation_id:
            raise ValueError("Missing conversation_id parameter in the request.")

        if conversation_id not in conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found.")

        conversation_data = [
            {"role": message.get_role(), "message": message.get_content()}
            for message in conversations[conversation_id].get_messages()
        ]

        return jsonify({"result": True, "conversation": conversation_data})

    except Exception as e:
        return jsonify({"result": False, "error": str(e)})


@app.route("/get_model_info", methods=["GET"])
def get_model_info():
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
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/generate_response", methods=["POST"])
def generate_response():
    try:
        data = request.get_json()
        conversation_id = data.get("conversation_id")
        user_message = data.get("message")
        max_tokens = data.get("max_tokens")
        single_message_mode = data.get("single_message_mode")

        timestamp = datetime.datetime.now()
        selected_files = data.get("selected_files")

        metadata = MessageMetadata(timestamp, selected_files)

        if not conversation_id or not user_message:
            raise ValueError("Missing conversation_id or message in the request.")

        if conversation_id not in conversations:
            raise ValueError(f"Conversation with id {conversation_id} not found.")

        conversations[conversation_id].add_user_message(user_message, metadata)

        response = conversations[conversation_id].generate_message(
            model_manager.models[0], max_tokens, single_message_mode
        )

        return jsonify({"result": True, "response": response})

    except Exception as e:
        return jsonify({"result": False, "error": str(e)})


def get_model_manager(mock_llama=False):
    if mock_llama:
        print("WARNING: Mock Mode")
    else:
        llamacpp_path = os.path.join("bin", "server.exe")

        if not os.path.exists(llamacpp_path):
            print(
                "Error:",
                "Add the llama.cpp server binary and llama.dll into the bin folder. See https://github.com/ggerganov/llama.cpp.",
            )
            sys.exit(-1)

        gguf_models = list(filter(lambda f: f.endswith(".gguf"), os.listdir("models")))

        if not gguf_models:
            print("Error: Add one or more gguf models to the models folder.")
            sys.exit(-1)

        model_manager = ModelManager(
            llamacpp_path,
            8000,
            gguf_models,
        )

        return model_manager


mock_llama = False

if __name__ == "__main__":
    # load_model_manager(mock_llama)

    if mock_llama:
        print("WARNING: Mock Mode")
    else:
        model_manager = get_model_manager(mock_llama)

        model_manager.load_model()

        import atexit

        # Increase the likelihood that the model manager is cleaned up properly
        atexit.register(model_manager.__del__)

    app.run(debug=False, port=17173)
