import torch
import uuid
import os
from TTS.api import TTS  # type: ignore


class TextToSpeechEngine:
    def __init__(self) -> None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    def text_to_speech(self, text: str) -> str:
        output_folder = "output"
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)
        output_path = os.path.join(output_folder, f"{uuid.uuid4()}.wav")

        self.tts.tts_to_file(  # type: ignore
            text, speaker_wav="example_audio.wav", file_path=output_path, language="en"
        )
        return output_path
