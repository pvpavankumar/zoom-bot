
import asyncio
import logging
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import tempfile
import threading
import queue
import time
import io
import wave
from typing import Optional, Callable, AsyncGenerator, Dict, List, Any
from datetime import datetime
from pathlib import Path

from ..core.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class UnifiedAudioProcessor:

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        device: Optional[int] = None
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device = device

        self.is_recording = False
        self.is_processing = False
        self.audio_queue = queue.Queue()
        self.stream = None

        self.recognizer = sr.Recognizer()
        self._configure_recognizer()

        self.audio_buffer: List[np.ndarray] = []
        self.speech_buffers: Dict[str, bytearray] = {}
        self.transcripts: List[dict] = []

        self.energy_threshold = 0.01
        self.silence_threshold = 1.0
        self.min_audio_duration = 0.5

        logger.info(f"Initialized UnifiedAudioProcessor: {sample_rate}Hz, {channels}ch, device={device}")

    def _configure_recognizer(self):
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5

    def list_audio_devices(self) -> Dict[str, Any]:
        try:
            devices = sd.query_devices()
            input_devices = []

            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate']
                    })

            logger.info(f"Found {len(input_devices)} input devices")
            return {
                'default_device': sd.default.device[0] if sd.default.device else None,
                'devices': input_devices
            }
        except Exception as e:
            logger.error(f"Error listing audio devices: {e}")
            return {'default_device': None, 'devices': []}

    def audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        if status:
            logger.warning(f"Audio callback status: {status}")

        audio_data = (indata[:, 0] * 32767).astype(np.int16)
        self.audio_queue.put(audio_data.copy())

    def start_recording(self) -> bool:
        try:
            device_info = self.list_audio_devices()
            if not device_info['devices']:
                logger.error("No audio input devices found")
                return False

            self.is_recording = True
            self.stream = sd.InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=self.audio_callback,
                dtype=np.float32
            )
            self.stream.start()
            logger.info("Audio recording started")
            return True

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False

    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        logger.info("Audio recording stopped")

    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def create_audio_data(self, audio_array: np.ndarray) -> sr.AudioData:
        if audio_array.dtype == np.float32:
            audio_int16 = (audio_array * 32767).astype(np.int16)
        else:
            audio_int16 = audio_array.astype(np.int16)

        return sr.AudioData(audio_int16.tobytes(), self.sample_rate, 2)

    def detect_voice_activity(self, audio_chunk: np.ndarray) -> bool:
        energy = np.mean(np.abs(audio_chunk))
        return energy > self.energy_threshold

    def recognize_speech(self, audio_data: sr.AudioData, engine: str = "google") -> Optional[str]:
        try:
            if engine == "google":
                return self.recognizer.recognize_google(audio_data)
            elif engine == "sphinx":
                return self.recognizer.recognize_sphinx(audio_data)
            else:
                logger.warning(f"Unknown recognition engine: {engine}")
                return None
        except sr.UnknownValueError:
            logger.debug("Speech recognition could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return None

    async def process_audio_stream(
        self,
        callback: Callable[[str], None],
        min_duration: float = 0.5,
        max_silence: float = 1.0
    ):
        """Process continuous audio stream with speech recognition."""
        if not self.start_recording():
            raise RuntimeError("Failed to start audio recording")

        self.is_processing = True
        audio_buffer = []
        last_speech_time = time.time()

        logger.info("Starting audio stream processing...")

        try:
            while self.is_processing and self.is_recording:
                chunk = self.get_audio_chunk(timeout=0.1)
                if chunk is not None:
                    audio_buffer.append(chunk)

                    if self.detect_voice_activity(chunk):
                        last_speech_time = time.time()

                current_time = time.time()
                buffer_duration = len(audio_buffer) * self.chunk_size / self.sample_rate
                silence_duration = current_time - last_speech_time

                if (buffer_duration >= min_duration and
                    (silence_duration >= max_silence or buffer_duration >= 10.0)):

                    if audio_buffer:
                        await self._process_audio_buffer(audio_buffer, callback)
                        audio_buffer = []
                        last_speech_time = time.time()

                await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Error in audio stream processing: {e}")
        finally:
            self.stop_recording()
            self.is_processing = False

    async def _process_audio_buffer(
        self,
        audio_buffer: List[np.ndarray],
        callback: Callable[[str], None]
    ):
        """Process audio buffer and extract text."""
        try:
            audio_data = np.concatenate(audio_buffer)

            audio_sr_data = self.create_audio_data(audio_data)

            text = await asyncio.get_event_loop().run_in_executor(
                None, self.recognize_speech, audio_sr_data, "google"
            )

            if text:
                logger.info(f"Recognized speech: {text}")

                transcript = {
                    'text': text,
                    'timestamp': datetime.now(),
                    'duration': len(audio_data) / self.sample_rate,
                    'confidence': 1.0
                }
                self.transcripts.append(transcript)

                if callback:
                    callback(text)

        except Exception as e:
            logger.error(f"Error processing audio buffer: {e}")

    def stop_processing(self):
        self.is_processing = False
        self.stop_recording()

    def get_recent_transcripts(self, count: int = 10) -> List[dict]:
        return self.transcripts[-count:] if self.transcripts else []

    def clear_transcripts(self):
        self.transcripts.clear()
        logger.info("Transcripts cleared")


class SoundDeviceMicrophone:

    def __init__(self, device_index: Optional[int] = None, sample_rate: int = 16000):
        self.device_index = device_index
        self.sample_rate = sample_rate

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def listen(
        self,
        recognizer: sr.Recognizer,
        timeout: Optional[float] = None,
        phrase_time_limit: Optional[float] = None
    ) -> sr.AudioData:
        """Listen for audio using SoundDevice (PyAudio-free)."""
        try:
            duration = phrase_time_limit if phrase_time_limit else 5.0

            logger.info(f"Recording audio for {duration} seconds...")
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                device=self.device_index,
                dtype=np.float32
            )
            sd.wait()

            audio_int16 = (audio_data[:, 0] * 32767).astype(np.int16)
            return sr.AudioData(audio_int16.tobytes(), self.sample_rate, 2)

        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            raise


def create_audio_processor(**kwargs) -> UnifiedAudioProcessor:
    return UnifiedAudioProcessor(**kwargs)

def list_audio_devices() -> Dict[str, Any]:
    processor = UnifiedAudioProcessor()
    return processor.list_audio_devices()

def test_audio_system() -> bool:
    try:
        processor = UnifiedAudioProcessor()
        devices = processor.list_audio_devices()
        return len(devices['devices']) > 0
    except Exception as e:
        logger.error(f"Audio system test failed: {e}")
        return False
