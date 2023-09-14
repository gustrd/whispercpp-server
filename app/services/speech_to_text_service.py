import os
import threading
from pywhispercpp.model import Model as WhisperModel

STT_MODEL = os.getenv('STT_MODEL')
STT_THREADS = int(os.getenv('STT_THREADS'))

class SingletonWhisperModel:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None and STT_MODEL:
                cls._instance = WhisperModel(STT_MODEL, STT_THREADS)
        return cls._instance

class SpeechToTextService:
    transcribe_lock = threading.Lock()

    @staticmethod
    def audio_path_to_text(audio_path: str, requests_dict={}) -> str:
        key = audio_path.replace('\\','')
        requests_dict[key] = None

        with SpeechToTextService.transcribe_lock:
            whisper_model = SingletonWhisperModel.get_instance()
            segments = whisper_model.transcribe(
                    audio_path, 
                    language='auto',
                    speed_up=True)
        output_string = ' '.join(segment.text for segment in segments)

        requests_dict[key] = output_string
        os.remove(audio_path)

        return output_string
    
    
