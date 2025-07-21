
import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
import io
import wave
import threading
import queue

print("0000000000000")
from .unified_processor import UnifiedAudioProcessor
from ..core.config import settings
print("completed p1")
from ..utils.logging import get_logger

logger = get_logger(__name__)
print("1111111111111")


class AudioProcessor:

    def __init__(self, instance_id: str, on_transcript: Optional[Callable] = None):
        print("2222222222222")
        self.instance_id = instance_id
        self.unified_processor = UnifiedAudioProcessor()
        print("completed p2")

        self.sample_rate = settings.audio_sample_rate
        self.chunk_size = settings.audio_chunk_size
        print("3333333333333")
        self.format = settings.audio_format

        self.audio_buffer: Dict[str, List[bytes]] = {}
        self.last_speech_time: Dict[str, datetime] = {}
        self.speaking_status: Dict[str, bool] = {}
        self.audio_levels: Dict[str, float] = {}

        self.speech_buffers: Dict[str, bytearray] = {}
        self.transcripts: Dict[str, List[dict]] = {}
        self.processing_queue = queue.Queue()
        self.processing_thread = None
        self.is_processing = False

        self.vad_threshold = settings.voice_activity_detection_threshold
        self.min_speech_duration = 0.5
        self.max_silence_duration = 2.0
        self.buffer_duration = 3.0

        self.on_transcript = on_transcript

        self.audio_enabled = settings.enable_audio_processing
        if not self.audio_enabled:
            logger.warning(f"Audio processing disabled for instance {instance_id}")

        logger.info(f"AudioProcessor (legacy wrapper) initialized for instance {instance_id}")

    async def initialize(self):
        logger.info("Initializing AudioProcessor components (legacy wrapper)...")

        await self.unified_processor.initialize()

        if self.audio_enabled:
            self.is_processing = True
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()
            logger.info("Audio processing thread started")

        logger.info("AudioProcessor components initialized")

    async def cleanup(self):
        self.is_processing = False
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)

        await self.unified_processor.cleanup()

        self.audio_buffer.clear()
        self.last_speech_time.clear()
        self.speaking_status.clear()
        self.audio_levels.clear()

        logger.info("AudioProcessor cleaned up")

    def _processing_loop(self):
        while self.is_processing:
            try:
                if hasattr(self, 'processing_queue'):
                    try:
                        item = self.processing_queue.get(timeout=0.1)
                        self.processing_queue.task_done()
                    except queue.Empty:
                        continue
                else:
                    import time
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                import time
                time.sleep(0.1)

    async def process_audio(self, audio_data: bytes, participant_id: str):
        try:
            audio_level = self._calculate_audio_level(audio_data)
            self.audio_levels[participant_id] = audio_level

            is_speaking = self._detect_voice_activity(audio_data, audio_level)

            current_time = datetime.utcnow()
            was_speaking = self.speaking_status.get(participant_id, False)

            if is_speaking:
                self.speaking_status[participant_id] = True
                self.last_speech_time[participant_id] = current_time

                if participant_id not in self.audio_buffer:
                    self.audio_buffer[participant_id] = []

                self.audio_buffer[participant_id].append(audio_data)

                if len(self.audio_buffer[participant_id]) >= 10:
                    await self._process_speech_buffer(participant_id)

            elif was_speaking:
                self.speaking_status[participant_id] = False
                if participant_id in self.audio_buffer:
                    await self._process_speech_buffer(participant_id)

            if was_speaking != is_speaking:
                from ..utils.logging import log_audio_event
                log_audio_event(
                    "speaking_status_changed",
                    self.instance_id,
                    participant_id,
                    is_speaking=is_speaking,
                    audio_level=audio_level
                )

        except Exception as e:
            logger.error(f"Error processing audio for {participant_id}: {e}")

    async def process_pending_audio(self):
        current_time = datetime.utcnow()

        for participant_id in list(self.audio_buffer.keys()):
            last_speech = self.last_speech_time.get(participant_id)

            if last_speech:
                silence_duration = (current_time - last_speech).total_seconds()

                if silence_duration > self.max_silence_duration:
                    await self._process_speech_buffer(participant_id)
                    self.speaking_status[participant_id] = False

    async def get_participant_status(self, participant_id: str) -> Dict[str, Any]:
        return {
            "is_speaking": self.speaking_status.get(participant_id, False),
            "audio_level": self.audio_levels.get(participant_id, 0.0),
            "last_speech_time": self.last_speech_time.get(participant_id),
            "buffer_size": len(self.audio_buffer.get(participant_id, []))
        }

    async def get_all_participants_status(self) -> Dict[str, Dict[str, Any]]:
        status = {}
        all_participants = set()
        all_participants.update(self.speaking_status.keys())
        all_participants.update(self.audio_levels.keys())

        for participant_id in all_participants:
            status[participant_id] = await self.get_participant_status(participant_id)

        return status

    def _calculate_audio_level(self, audio_data: bytes) -> float:
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            if len(audio_array) == 0:
                return 0.0

            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))

            max_value = 32767.0
            normalized_level = min(rms / max_value, 1.0)

            return float(normalized_level)

        except Exception as e:
            logger.error(f"Error calculating audio level: {e}")
            return 0.0

    def _detect_voice_activity(self, audio_data: bytes, audio_level: float) -> bool:
        if audio_level < self.vad_threshold:
            return False

        try:
            import webrtcvad
            vad = webrtcvad.Vad(2)

            if self.sample_rate in [8000, 16000, 32000, 48000]:
                frame_duration = 30
                frame_size = int(self.sample_rate * frame_duration / 1000)

                if len(audio_data) >= frame_size * 2:
                    frame = audio_data[:frame_size * 2]
                    return vad.is_speech(frame, self.sample_rate)

        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"VAD error: {e}")

        return audio_level > self.vad_threshold

    async def _process_speech_buffer(self, participant_id: str):
        if participant_id not in self.audio_buffer or not self.audio_buffer[participant_id]:
            return

        try:
            combined_audio = b''.join(self.audio_buffer[participant_id])

            self.audio_buffer[participant_id] = []

            transcript = await self.unified_processor.transcribe_audio(combined_audio)

            if transcript and transcript.strip():
                logger.debug(f"Transcribed speech from {participant_id}: {transcript[:50]}...")

                await self._handle_transcript(participant_id, transcript)

                from ..utils.logging import log_audio_event
                log_audio_event(
                    "speech_transcribed",
                    self.instance_id,
                    participant_id,
                    transcript_length=len(transcript),
                    words_count=len(transcript.split())
                )

        except Exception as e:
            logger.error(f"Error processing speech buffer for {participant_id}: {e}")

    async def _handle_transcript(self, participant_id: str, transcript: str):
        from ..core.config import settings
        import redis
        import json

        try:
            redis_client = redis.from_url(settings.redis_url)

            transcript_data = {
                "participant_id": participant_id,
                "transcript": transcript,
                "timestamp": datetime.utcnow().isoformat(),
                "instance_id": self.instance_id
            }

            key = f"transcript:{self.instance_id}"
            redis_client.lpush(key, json.dumps(transcript_data))
            redis_client.expire(key, 3600)

            from ..tasks.room_tasks import analyze_conversation_task
            analyze_conversation_task.delay(
                transcript=transcript,
                participants={participant_id: {"last_speech": transcript}},
                room_id=self.instance_id
            )

        except Exception as e:
            logger.error(f"Error handling transcript: {e}")


def process_audio_chunk(audio_data: bytes, participant_id: str, room_id: str, timestamp: float) -> Dict[str, Any]:
    try:
        processor = AudioProcessor(room_id)

        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        if len(audio_array) > 0:
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            max_value = 32767.0
            audio_level = min(rms / max_value, 1.0)
        else:
            audio_level = 0.0

        is_speech = audio_level > settings.voice_activity_detection_threshold

        return {
            "participant_id": participant_id,
            "audio_level": float(audio_level),
            "is_speech": is_speech,
            "timestamp": timestamp,
            "chunk_size": len(audio_data)
        }

    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}")
        return {
            "participant_id": participant_id,
            "error": str(e),
            "timestamp": timestamp
        }
