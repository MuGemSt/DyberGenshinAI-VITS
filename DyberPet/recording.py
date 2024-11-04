# coding:utf-8
import wave
import torch
import whisper
import pyaudio
import tempfile
from PySide6.QtCore import Signal, QThread


class AudioRecorder(QThread):
    finished = Signal(str, name="rec_finished")
    failed = Signal(str, name="rec_failed")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording = False
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.model = whisper.load_model(
            "base", device="cuda" if torch.cuda.is_available() else "cpu"
        )

    def run(self):
        frames = []
        while self.recording:
            data = self.stream.read(self.CHUNK)
            frames.append(data)

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        wf = wave.open(self.tempfile.name, "wb")
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b"".join(frames))
        wf.close()

        txt = self._transcribe_audio(self.tempfile.name)
        self.finished.emit(txt)

    def _create_audio_stream(self):
        p = pyaudio.PyAudio()
        stream = p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.RATE,
        )
        return p, stream

    def _transcribe_audio(self, file_name):
        result = self.model.transcribe(
            file_name, fp16=False, language="zh", initial_prompt="以下是普通话的句子"
        )
        return result["text"]

    # slot
    def start_recording(self):
        self.recording = True
        self.tempfile = tempfile.NamedTemporaryFile(delete=False)
        try:
            self.p, self.stream = self._create_audio_stream()
        except OSError:
            self.recording = False
            self.failed.emit("请打开麦克风权限")
            return

        self.start()

    # slot
    def stop_recording(self):
        self.recording = False
