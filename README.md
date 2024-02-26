# assistant-coder

A system and architecture for an assistant coder that amongst other things can be used to generate coding solutions using large language models.

## Features
* Flask server that handles multiple conversations.
* Support for simple tools (browse/search web, read files, retrieve time and date).
* Support for knowledge retrieval (using embeddings and vector stores).
* Suggestion system where the assistant suggests follow-up questions.
* Safety system where the assistant asks for access to files and Internet use.
* Support for using the clipboard as input to the assistant.
* Simple gradio client for basic chatbot use.
* PyQt6 client for more advanced coding purposes.

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
```
pip install -r requirements.txt
```


## Running

Make sure you first download a gguf-model ([Mistral-7B is highly recommended](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)) and put it in the models folder. You will also need to put a llama.cpp-server binary in the bin folder. After that run the server using one of the following commands:

```bash
python server.py
python3 server.py
```

## Tests

You can run the unit tests using the following command:
```
python -m unittest discover
```