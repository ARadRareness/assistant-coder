# assistant-coder

A system and architecture for generating coding solutions using large language models.

## Features
* Flask server that handles multiple conversations.
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

Make sure you first download a gguf-model and put it in the models folder. You will also need to put a llama.cpp-server binary in the bin folder. After that run the server using one of the following commands:

```bash
python server.py
python3 server.py
```

## Tests

You can run the unit tests using the following command:
```
python -m unittest discover
```