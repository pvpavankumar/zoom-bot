
import asyncio
import time
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.audio import UnifiedAudioProcessor, SoundDeviceMicrophone
from src.audio.processing import AudioProcessor
from src.core.room_bot import RoomBot
from src.tasks.room_tasks import process_audio_task


class TestAudioCapture:

    def setup_method(self):
        self.sample_rate = 16000
        self.channels = 1
        self.test_duration = 2.0

    def test_audio_device_detection(self):
        try:
            processor = UnifiedAudioProcessor()
            devices = processor.list_audio_devices()

            assert devices is not None
            assert 'devices' in devices
            assert len(devices['devices']) > 0

            input_devices = [d for d in devices['devices'] if d.get('max_input_channels', 0) > 0]
            assert len(input_devices) > 0

            print(f"✅ Found {len(input_devices)} input audio devices")
            print(f"📊 Default device: {devices.get('default_device', 'None')}")

        except Exception as e:
            print(f"❌ Audio device detection failed: {e}")
            raise

    def test_unified_audio_processor_initialization(self):
        try:
            processor = UnifiedAudioProcessor(
                sample_rate=self.sample_rate,
                channels=self.channels,
                device=None
            )

            assert processor.sample_rate == self.sample_rate
            assert processor.channels == self.channels
            assert processor.device_id is not None or processor.device_id == -1

            print("✅ UnifiedAudioProcessor initialized successfully")

        except Exception as e:
            print(f"❌ UnifiedAudioProcessor initialization failed: {e}")
            raise

    def test_mock_audio_stream(self):
        try:
            duration_samples = int(self.sample_rate * self.test_duration)
            mock_audio = np.random.normal(0, 0.01, duration_samples).astype(np.float32)

            speech_start = int(0.5 * self.sample_rate)
            speech_end = int(1.5 * self.sample_rate)
            mock_audio[speech_start:speech_end] += np.random.normal(0, 0.1, speech_end - speech_start)

            audio_int16 = (mock_audio * 32767).astype(np.int16)

            assert len(audio_int16) == duration_samples
            assert audio_int16.dtype == np.int16

            print(f"✅ Generated {self.test_duration}s of mock audio data")
            print(f"📊 Audio shape: {audio_int16.shape}, Range: [{audio_int16.min()}, {audio_int16.max()}]")

        except Exception as e:
            print(f"❌ Mock audio stream test failed: {e}")
            raise


class TestVoiceActivityDetection:

    def setup_method(self):
        self.processor = UnifiedAudioProcessor()
        self.sample_rate = 16000

    def test_vad_silence_detection(self):
        try:
            silence_duration = 1.0
            silence_samples = int(self.sample_rate * silence_duration)
            silence_audio = np.zeros(silence_samples, dtype=np.int16)

            has_voice = self.processor.detect_voice_activity(silence_audio)
            assert has_voice == False

            print("✅ VAD correctly detected silence")

        except Exception as e:
            print(f"❌ VAD silence detection failed: {e}")
            raise

    def test_vad_speech_detection(self):
        try:
            speech_duration = 1.0
            speech_samples = int(self.sample_rate * speech_duration)

            speech_audio = np.random.normal(0, 0.3, speech_samples)
            speech_audio = (speech_audio * 32767 * 0.5).astype(np.int16)

            has_voice = self.processor.detect_voice_activity(speech_audio)
            assert has_voice == True

            print("✅ VAD correctly detected speech activity")

        except Exception as e:
            print(f"❌ VAD speech detection failed: {e}")
            raise

    def test_vad_mixed_audio(self):
        try:
            total_duration = 3.0
            segment_duration = 1.0
            segment_samples = int(self.sample_rate * segment_duration)

            silence = np.zeros(segment_samples, dtype=np.int16)

            speech = np.random.normal(0, 0.3, segment_samples)
            speech = (speech * 32767 * 0.4).astype(np.int16)

            vad_results = []
            segments = [silence, speech, silence]
            segment_names = ["silence", "speech", "silence"]

            for i, (segment, name) in enumerate(zip(segments, segment_names)):
                has_voice = self.processor.detect_voice_activity(segment)
                vad_results.append(has_voice)
                print(f"📊 Segment {i+1} ({name}): Voice detected = {has_voice}")

            assert vad_results[0] == False
            assert vad_results[1] == True
            assert vad_results[2] == False

            print("✅ VAD correctly processed mixed audio")

        except Exception as e:
            print(f"❌ VAD mixed audio test failed: {e}")
            raise


class TestMultiRoomAudioMonitoring:

    def setup_method(self):
        self.room_configs = [
            {"room_id": "room_1", "participants": ["interviewer_1", "candidate_1"]},
            {"room_id": "room_2", "participants": ["interviewer_2", "candidate_2"]},
            {"room_id": "room_3", "participants": ["interviewer_3", "candidate_3"]},
        ]
        self.audio_processors = {}

    async def test_multi_room_processor_creation(self):
        try:
            for room_config in self.room_configs:
                room_id = room_config["room_id"]

                processor = AudioProcessor(instance_id=room_id)
                await processor.initialize()

                self.audio_processors[room_id] = processor
                print(f"✅ Audio processor created for {room_id}")

            assert len(self.audio_processors) == 3
            print("✅ All room audio processors initialized")

        except Exception as e:
            print(f"❌ Multi-room processor creation failed: {e}")
            raise

    async def test_simultaneous_audio_processing(self):
        try:
            tasks = []

            for room_config in self.room_configs:
                room_id = room_config["room_id"]
                participants = room_config["participants"]

                task = self._process_room_audio(room_id, participants)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_rooms = sum(1 for result in results if not isinstance(result, Exception))
            assert successful_rooms == 3

            print(f"✅ Successfully processed audio for {successful_rooms} rooms simultaneously")

        except Exception as e:
            print(f"❌ Simultaneous audio processing failed: {e}")
            raise

    async def _process_room_audio(self, room_id, participants):
        try:
            processor = self.audio_processors.get(room_id)
            if not processor:
                raise ValueError(f"No processor found for {room_id}")

            for participant in participants:
                audio_data = self._generate_mock_audio(participant)

                await processor.process_audio(audio_data, participant)

                await asyncio.sleep(0.1)

            print(f"📊 Processed audio for {len(participants)} participants in {room_id}")
            return True

        except Exception as e:
            print(f"❌ Audio processing failed for {room_id}: {e}")
            raise

    def _generate_mock_audio(self, participant_type):
        duration = 0.5
        samples = int(16000 * duration)

        if "interviewer" in participant_type:
            audio = np.random.normal(0, 0.2, samples)
        else:
            audio = np.random.normal(0, 0.25, samples)

        audio_int16 = (audio * 32767).astype(np.int16)
        return audio_int16.tobytes()

    async def test_audio_quality_monitoring(self):
        try:
            quality_metrics = {}

            for room_id in self.audio_processors:
                processor = self.audio_processors[room_id]

                room_status = await processor.get_all_participants_status()

                avg_audio_level = 0.0
                active_participants = 0

                for participant_id, status in room_status.items():
                    if status.get('audio_level', 0) > 0:
                        avg_audio_level += status['audio_level']
                        active_participants += 1

                if active_participants > 0:
                    avg_audio_level /= active_participants

                quality_metrics[room_id] = {
                    "avg_audio_level": avg_audio_level,
                    "active_participants": active_participants,
                    "quality_score": min(avg_audio_level * 100, 100)
                }

                print(f"📊 {room_id}: Quality score = {quality_metrics[room_id]['quality_score']:.1f}%")

            assert len(quality_metrics) == 3
            print("✅ Audio quality monitoring working across all rooms")

        except Exception as e:
            print(f"❌ Audio quality monitoring failed: {e}")
            raise

    async def cleanup(self):
        for processor in self.audio_processors.values():
            try:
                await processor.cleanup()
            except:
                pass


class TestAudioPerformance:

    async def test_processing_latency(self):
        try:
            processor = UnifiedAudioProcessor()

            latencies = []

            for i in range(10):
                audio_data = np.random.normal(0, 0.1, 8000).astype(np.float32)

                start_time = time.perf_counter()

                has_voice = processor.detect_voice_activity(audio_data)

                end_time = time.perf_counter()
                latency = (end_time - start_time) * 1000
                latencies.append(latency)

            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)

            print(f"📊 Audio processing latency:")
            print(f"   Average: {avg_latency:.2f}ms")
            print(f"   Maximum: {max_latency:.2f}ms")

            assert avg_latency < 100
            assert max_latency < 200

            print("✅ Audio processing latency within acceptable limits")

        except Exception as e:
            print(f"❌ Audio performance test failed: {e}")
            raise


async def run_audio_monitoring_tests():

    print("🎤 ZOOM INTERVIEW BOT - AUDIO MONITORING TESTS")
    print("=" * 60)
    print()

    try:
        print("🎧 Testing Audio Capture...")
        capture_test = TestAudioCapture()
        capture_test.setup_method()
        capture_test.test_audio_device_detection()
        capture_test.test_unified_audio_processor_initialization()
        capture_test.test_mock_audio_stream()
        print("✅ Audio capture tests completed\n")

        print("🗣️ Testing Voice Activity Detection...")
        vad_test = TestVoiceActivityDetection()
        vad_test.setup_method()
        vad_test.test_vad_silence_detection()
        vad_test.test_vad_speech_detection()
        vad_test.test_vad_mixed_audio()
        print("✅ VAD tests completed\n")

        print("🏠 Testing Multi-Room Audio Monitoring...")
        multi_room_test = TestMultiRoomAudioMonitoring()
        multi_room_test.setup_method()
        await multi_room_test.test_multi_room_processor_creation()
        await multi_room_test.test_simultaneous_audio_processing()
        await multi_room_test.test_audio_quality_monitoring()
        await multi_room_test.cleanup()
        print("✅ Multi-room monitoring tests completed\n")

        print("⚡ Testing Audio Performance...")
        performance_test = TestAudioPerformance()
        await performance_test.test_processing_latency()
        print("✅ Performance tests completed\n")

        print("🎉 ALL AUDIO MONITORING TESTS PASSED!")
        print("✅ Audio capture and device detection working")
        print("✅ Voice activity detection accurate")
        print("✅ Multi-room simultaneous monitoring operational")
        print("✅ Audio processing performance within limits")

    except Exception as e:
        print(f"❌ Audio monitoring test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_audio_monitoring_tests())
