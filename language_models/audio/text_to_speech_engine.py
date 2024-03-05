from typing import List
import torch
import hashlib
import os
import subprocess
from TTS.api import TTS  # type: ignore
import spacy


class TextToSpeechEngine:
    def __init__(self) -> None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print("TTS IS USING", device)
        self.tts = None
        if os.name == "posix":
            self.tts = None  # Use built in TTS with Mac
        else:
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    def text_to_speech(self, text: str) -> str:
        output_folder = "output"
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        md5sum = hashlib.md5(text.encode()).hexdigest()
        output_path = os.path.join(output_folder, f"{md5sum}.wav")

        if not os.path.exists(output_path):
            if self.tts is None:
                self.text_to_speech_mac(text, output_path)
            else:
                self.tts.tts_to_file(  # type: ignore
                    text,
                    speaker_wav="example_audio.wav",
                    file_path=output_path,
                    language="en",
                )
        return output_path

    def text_to_speech_mac(self, text: str, output_path: str) -> None:
        subprocess.run(
            [
                "say",
                "-v",
                "Karen (Premium)",
                "-o",
                output_path,
                "--data-format=LEF32@22050",
                text,
            ]
        )

        if not os.path.exists(output_path):
            subprocess.run(
                [
                    "say",
                    "-o",
                    output_path,
                    "--data-format=LEF32@22050",
                    text,
                ]
            )

    def text_to_speech_with_split(self, text: str):
        try:
            nlp = spacy.load("en_core_web_sm")
        except:
            from spacy.cli import download  # type: ignore

            download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

        doc = nlp(text)

        sentences: List[str] = []
        current_sentence: str = ""
        for sentence in doc.sents:
            current_sentence += sentence.text
            if len(current_sentence) > 20:
                sentences.append(current_sentence)
                current_sentence = ""
        if current_sentence:
            sentences.append(current_sentence)

        for sentence in sentences:
            yield self.text_to_speech(sentence)
