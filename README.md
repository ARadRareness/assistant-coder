# assistant-coder

A system architecture for a completely offline AI assistant that amongst other things can be used to chat and generate coding solutions using large language models.

## Features
* Flask server that handles multiple conversations.
* Support for simple tools (browse/search web, read files, retrieve time and date).
* Support for knowledge retrieval (using embeddings and vector stores).
* Suggestion system where the assistant can suggest follow-up questions.
* Safety system where the assistant asks for permission to access files and the internet.
* A basic code interpreter for problem solving.
* Support for using the clipboard as input to the assistant.
* Streamed text to speech playback using XTTS v2 or 'say' command for Mac systems.
* Simple gradio client for basic chatbot uses.
* PySide6 client for more advanced chatbot uses.

## How to install

### 1. Clone this repository
```
git clone https://github.com/ARadRareness/assistant-coder.git
```

### 2. (Optionally) Create a conda environment.
```
conda create -n ac
```

### 3. (Optionally) Activate the environment.
```
conda activate ac
```

### 4. Install requirements
For Windows using CUDA, install the following requirements
```
python -m pip install torch torchvision torchaudio --index-url http://download.pytorch.org/whl/cu118 --trusted-host download.pytorch.org
python -m pip install https://github.com/jllllll/bitsandbytes-windows-webui/releases/download/wheels/bitsandbytes-0.41.1-py3-none-win_amd64.whl
```

Then run the following command to install the rest of the requirements
```
pip install -r requirements.txt
```


## Running

Make sure you first download a gguf-model ([Mistral-7B is highly recommended](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)) and put it in the models folder. You will also need to put a llama.cpp-server binary in the bin folder. After that run the server using one of the following commands:

```bash
python server.py
python3 server.py
```

Then run the desktop client with:

```bash
python client\desktop_client.py
python3 client/desktop_client.py
```

## Tests

You can run the unit tests using the following command:
```
python -m unittest discover
```