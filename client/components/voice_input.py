try:
    from typing import Optional
    from faster_whisper import WhisperModel
    import numpy as np
    import pyaudio
    import webrtcvad

    import datetime
    import os
    import queue
    import threading
    import wave

    IMPORT_SUCCESS = True
except ImportError as e:
    print(e)
    IMPORT_SUCCESS = False


class ThreadSafeBoolean:
    def __init__(self, initial_value=False):
        self._value = initial_value
        self._lock = threading.Lock()

    def set(self, value):
        with self._lock:
            self._value = value

    def get(self):
        with self._lock:
            return self._value


class VoiceInput:
    def __init__(self, use_local_whisper=True):
        self.message_queue = queue.Queue()
        self.quit_flag = ThreadSafeBoolean(False)
        self.voice_input_thread = None

        if IMPORT_SUCCESS:
            self.voice_input_thread = VoiceInputThread(
                self.message_queue, self.quit_flag, use_local_whisper=use_local_whisper
            )

    def __del__(self):
        if self.voice_input_thread:
            self.quit_flag.set(True)
            self.voice_input_thread.join()

    def get_input(self) -> Optional[str]:
        if not IMPORT_SUCCESS:
            return None
        return self.message_queue.get(block=False)


class VoiceInputThread(threading.Thread):
    def __init__(self, message_queue, quit_flag, language="en", use_local_whisper=True):
        threading.Thread.__init__(self)

        self.message_queue = message_queue
        self.quit_flag = quit_flag
        self.language = language
        self.use_local_whisper = use_local_whisper

        if self.use_local_whisper:
            self.model = WhisperModel("large-v2", device="cuda", compute_type="float16")

        print("THREAD STARTED")
        self.daemon = True
        self.start()

    def run(self):
        while not self.quit_flag.get():
            input_message = self.listen()
            if input_message:
                self.message_queue.put(input_message)

    def listen(self):
        text = ""
        initial_whisper_prompt = "DEFAULT"
        while (not text or text == initial_whisper_prompt) and not self.quit_flag.get():
            print("LISTENING")
            audio_data = self.capture_audio()
            print("AUDIO CAPTURED")
            fname = os.path.join(
                "wavs", datetime.datetime.now().strftime("input_%Y%m%d_%H%M%S.wav")
            )
            try:
                if not os.path.exists("wavs"):
                    os.mkdir("wavs")
            except:
                None
            self.save_audio_to_wav(audio_data, fname)
            if self.use_local_whisper:
                text = self.generate_transcript(fname, initial_whisper_prompt).strip()
            else:
                text = fname  # Directly use the filename if not using Whisper for transcription

            if not text:
                os.remove(fname)

        return text

    def capture_audio(self):
        chunk = 960  # number of audio samples per chunk
        sample_rate = 16000  # number of samples per second
        vad_aggressiveness = 3  # aggressiveness of VAD (0-3)

        input_device = 0  # 2

        # create a PyAudio object
        audio = pyaudio.PyAudio()
        # open a stream to capture audio input
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=input_device,
            frames_per_buffer=chunk,
        )

        # create a VAD object
        vad = webrtcvad.Vad(vad_aggressiveness)

        # start recording audio
        frames = []
        speech_timeout = 0

        # The recording usually get some trash at the beginning which we want to skip
        # for i in range(10):
        #    stream.read(chunk)

        has_speech = False

        while not self.quit_flag.get():
            # read a chunk of audio data from the stream
            data = stream.read(chunk)

            # convert the audio data to a numpy array
            signal = np.frombuffer(data, dtype=np.int16)

            # check if the signal contains speech
            if vad.is_speech(signal, sample_rate=sample_rate):
                # reset the speech timeout counter
                speech_timeout = 0
                has_speech = True
            else:
                # increment the speech timeout counter
                speech_timeout += 1

            if has_speech:
                frames.append(data)

            # if there has been no speech for more than 1 second, stop recording
            if has_speech and speech_timeout > sample_rate / chunk:
                break

        # stop recording audio and close the stream
        stream.stop_stream()
        stream.close()

        # terminate the PyAudio object
        audio.terminate()

        # return the recorded audio data
        return b"".join(frames)

    def save_audio_to_wav(self, audio_data, filename):
        # set the parameters for the WAV file
        nchannels = 1  # mono audio
        sampwidth = 2  # 16-bit audio
        framerate = 16000  # sample rate of audio data
        nframes = len(audio_data)

        # create the WAV file
        with wave.open(filename, "wb") as wav_file:
            wav_file.setparams(
                (nchannels, sampwidth, framerate, nframes, "NONE", "NONE")
            )
            wav_file.writeframes(audio_data)

    def generate_transcript(self, fname, initial_whisper_prompt):
        segments, _info = self.model.transcribe(
            fname,
            beam_size=5,
            initial_prompt=initial_whisper_prompt,
            language=self.language,
            vad_filter=True,
            # word_timestamps=True,
        )
        return " ".join([x.text for x in segments])

    def get_input_devices(self):
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        num_devices = info.get("deviceCount")
        for i in range(num_devices):
            if (
                p.get_device_info_by_host_api_device_index(0, i).get("maxInputChannels")
                > 0
            ):
                print(
                    "Input Device id ",
                    i,
                    " - ",
                    p.get_device_info_by_host_api_device_index(0, i).get("name"),
                )

                pass  # Placeholder for any additional logic needed here


if __name__ == "__main__":
    import time

    # Create an instance of the VoiceInput class with use_local_whisper set as needed
    voice_input = VoiceInput(use_local_whisper=True)

    while True:
        time.sleep(0.1)
        try:
            result = voice_input.get_input()
            if result:
                print(result)
        except Exception as e:
            None
            # print(e)
