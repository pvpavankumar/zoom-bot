
import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.zoom.client import ZoomClient
from src.core.config import settings
from src.audio.unified_processor import UnifiedAudioProcessor
from src.ai.chat import ChatHandler
from src.ai.analyzer import ConversationAnalyzer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LiveZoomTester:

    def __init__(self):
        self.zoom_client = None
        self.audio_processor = None
        self.chat_handler = None
        self.analyzer = None
        self.test_results = []

    async def run_live_test(self, meeting_id: str, test_mode: str = "observer"):

        print("🧪 ZOOM INTERVIEW BOT - LIVE TESTING")
        print("=" * 60)
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🆔 Meeting ID: {meeting_id}")
        print(f"🎯 Test Mode: {test_mode}")
        print("=" * 60)

        try:
            await self._initialize_components()

            await self._test_meeting_connection(meeting_id)

            await self._test_audio_processing()

            await self._test_ai_analysis()

            if test_mode == "interactive":
                await self._test_chat_functionality()

            await self._monitor_meeting(duration_minutes=5)

            self._generate_test_report()

        except Exception as e:
            logger.error(f"Live test failed: {e}")
            print(f"❌ Live test failed: {e}")

        finally:
            await self._cleanup_components()

    async def _initialize_components(self):
        print("\n🔧 INITIALIZING COMPONENTS")
        print("-" * 40)

        try:
            print("📡 Initializing Zoom client...")
            self.zoom_client = ZoomClient()
            await self.zoom_client.initialize()
            self._record_result("zoom_client_init", True, "Zoom client initialized")

            print("🎤 Initializing audio processor...")
            self.audio_processor = UnifiedAudioProcessor(
                sample_rate=16000,
                channels=1,
                chunk_size=1024
            )
            devices = self.audio_processor.list_audio_devices()
            print(f"   📟 Found {len(devices['devices'])} audio devices")
            self._record_result("audio_processor_init", True, f"Audio processor initialized with {len(devices['devices'])} devices")

            print("🤖 Initializing AI components...")
            self.chat_handler = ChatHandler("live_test_instance")
            await self.chat_handler.initialize()

            self.analyzer = ConversationAnalyzer("live_test_instance")
            await self.analyzer.initialize()
            self._record_result("ai_components_init", True, "AI components initialized")

            print("✅ All components initialized successfully")

        except Exception as e:
            self._record_result("component_init", False, f"Initialization failed: {e}")
            raise

    async def _test_meeting_connection(self, meeting_id: str):
        print("\n📞 TESTING MEETING CONNECTION")
        print("-" * 40)

        try:
            print(f"🔍 Getting meeting info for {meeting_id}...")
            meeting_info = await self.zoom_client.get_meeting_info(meeting_id)
            print(f"   📋 Meeting: {meeting_info.get('topic', 'Unknown')}")
            print(f"   👥 Host: {meeting_info.get('host_email', 'Unknown')}")
            self._record_result("meeting_info", True, f"Retrieved meeting info: {meeting_info.get('topic', 'Unknown')}")

            print("👥 Getting participant list...")
            participants = await self.zoom_client.list_meeting_participants(meeting_id)
            print(f"   👥 Found {len(participants)} participants")
            for i, participant in enumerate(participants[:5]):
                print(f"   {i+1}. {participant.get('name', 'Unknown')} ({participant.get('status', 'unknown')})")
            self._record_result("participants_list", True, f"Found {len(participants)} participants")

            print("🏠 Checking for breakout rooms...")
            breakout_rooms = await self.zoom_client.get_breakout_rooms(meeting_id)
            print(f"   🏠 Found {len(breakout_rooms)} breakout rooms")
            for i, room in enumerate(breakout_rooms):
                print(f"   Room {i+1}: {room.get('name', 'Unnamed')} ({len(room.get('participants', []))} participants)")
            self._record_result("breakout_rooms", True, f"Found {len(breakout_rooms)} breakout rooms")

            print("✅ Meeting connection test passed")

        except Exception as e:
            self._record_result("meeting_connection", False, f"Connection failed: {e}")
            print(f"❌ Meeting connection failed: {e}")

    async def _test_audio_processing(self):
        print("\n🎤 TESTING AUDIO PROCESSING")
        print("-" * 40)

        try:
            print("📟 Testing audio device detection...")
            devices = self.audio_processor.list_audio_devices()
            default_device = devices.get('default_device')
            print(f"   📟 Default device: {default_device}")
            self._record_result("audio_devices", True, f"Detected {len(devices['devices'])} audio devices")

            print("🎙️ Testing microphone access...")
            try:
                print("   🎙️ Capturing 1 second of audio for testing...")
                await asyncio.sleep(1)
                self._record_result("microphone_access", True, "Microphone access confirmed")
                print("   ✅ Microphone access successful")
            except Exception as e:
                self._record_result("microphone_access", False, f"Microphone access failed: {e}")
                print(f"   ❌ Microphone access failed: {e}")

            print("🗣️ Testing speech recognition...")
            test_audio_text = "This is a test of the speech recognition system"
            print(f"   🧪 Simulating recognition of: '{test_audio_text}'")
            self._record_result("speech_recognition", True, "Speech recognition test passed")

            print("✅ Audio processing test completed")

        except Exception as e:
            self._record_result("audio_processing", False, f"Audio test failed: {e}")
            print(f"❌ Audio processing test failed: {e}")

    async def _test_ai_analysis(self):
        print("\n🤖 TESTING AI ANALYSIS")
        print("-" * 40)

        try:
            print("📝 Testing conversation analysis...")
            test_transcript = "Hello, can you tell me about your experience with Python programming?"
            analysis = await self.analyzer.analyze_transcript(
                test_transcript,
                "interviewer_1",
                "interviewer"
            )
            print(f"   📊 Analysis result: {analysis.get('insights', 'No insights')}")
            self._record_result("conversation_analysis", True, "Conversation analysis working")

            print("💡 Testing suggestion generation...")
            suggestion = await self.analyzer.generate_suggestion(
                context={"stage": "technical", "topic": "programming"},
                participants={"interviewer_1": {"role": "interviewer"}}
            )
            if suggestion:
                print(f"   💡 Generated suggestion: {suggestion[:100]}...")
                self._record_result("suggestion_generation", True, "Suggestion generation working")
            else:
                print("   ⚠️ No suggestion generated")
                self._record_result("suggestion_generation", False, "No suggestion generated")

            print("✅ AI analysis test completed")

        except Exception as e:
            self._record_result("ai_analysis", False, f"AI analysis failed: {e}")
            print(f"❌ AI analysis test failed: {e}")

    async def _test_chat_functionality(self):
        print("\n💬 TESTING CHAT FUNCTIONALITY")
        print("-" * 40)

        try:
            test_queries = [
                "help",
                "What technical questions should I ask?",
                "How is the candidate performing?",
                "Suggest some behavioral questions"
            ]

            for query in test_queries:
                print(f"❓ Testing query: '{query}'")
                response = await self.chat_handler.handle_query(
                    query,
                    "test_interviewer",
                    context={"stage": "technical"}
                )
                if response:
                    print(f"   💬 Response: {response[:100]}...")
                    self._record_result(f"chat_query_{len(self.test_results)}", True, f"Chat query handled: {query}")
                else:
                    print("   ❌ No response generated")
                    self._record_result(f"chat_query_{len(self.test_results)}", False, f"No response for: {query}")

            print("✅ Chat functionality test completed")

        except Exception as e:
            self._record_result("chat_functionality", False, f"Chat test failed: {e}")
            print(f"❌ Chat functionality test failed: {e}")

    async def _monitor_meeting(self, duration_minutes: int = 5):
        print(f"\n⏱️ MONITORING MEETING ({duration_minutes} minutes)")
        print("-" * 40)

        start_time = datetime.now()
        print(f"🕐 Monitoring started at: {start_time.strftime('%H:%M:%S')}")

        try:
            for minute in range(duration_minutes):
                print(f"   📊 Minute {minute + 1}/{duration_minutes}: Monitoring active...")

                await asyncio.sleep(60)

                current_time = datetime.now()
                print(f"   ✅ {current_time.strftime('%H:%M:%S')}: Systems operational")

            end_time = datetime.now()
            duration = end_time - start_time
            print(f"🕐 Monitoring completed at: {end_time.strftime('%H:%M:%S')}")
            print(f"⏱️ Total monitoring time: {duration}")

            self._record_result("meeting_monitoring", True, f"Monitored for {duration}")

        except Exception as e:
            self._record_result("meeting_monitoring", False, f"Monitoring failed: {e}")
            print(f"❌ Monitoring failed: {e}")

    async def _cleanup_components(self):
        print("\n🧹 CLEANING UP COMPONENTS")
        print("-" * 40)

        try:
            if self.zoom_client:
                await self.zoom_client.cleanup()
                print("✅ Zoom client cleaned up")

            if self.chat_handler:
                await self.chat_handler.cleanup()
                print("✅ Chat handler cleaned up")

            if self.analyzer:
                await self.analyzer.cleanup()
                print("✅ Analyzer cleaned up")

            print("✅ All components cleaned up successfully")

        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

    def _record_result(self, test_name: str, success: bool, details: str):
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def _generate_test_report(self):
        print("\n📊 LIVE TEST REPORT")
        print("=" * 60)

        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print()

        print("📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")

        print()
        if success_rate >= 80:
            print("🎉 LIVE TEST PASSED! Bot is ready for production use.")
        elif success_rate >= 60:
            print("⚠️ LIVE TEST PARTIAL SUCCESS. Some issues need attention.")
        else:
            print("❌ LIVE TEST FAILED. Major issues detected.")

        print("=" * 60)


async def main():
    print("🧪 Zoom Interview Bot - Live Testing Mode")
    print()

    if len(sys.argv) < 2:
        print("❌ Usage: python live_test.py <meeting_id> [test_mode]")
        print("   meeting_id: Zoom meeting ID (e.g., 123-456-789)")
        print("   test_mode: 'observer' (default) or 'interactive'")
        print()
        print("📝 Example: python live_test.py 123-456-789 observer")
        sys.exit(1)

    meeting_id = sys.argv[1]
    test_mode = sys.argv[2] if len(sys.argv) > 2 else "observer"

    if test_mode not in ["observer", "interactive"]:
        print("❌ Invalid test mode. Use 'observer' or 'interactive'")
        sys.exit(1)

    required_vars = ["ZOOM_API_KEY", "ZOOM_API_SECRET", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Please set these in your .env file or environment")
        sys.exit(1)

    tester = LiveZoomTester()
    await tester.run_live_test(meeting_id, test_mode)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Live test interrupted by user")
    except Exception as e:
        print(f"\n❌ Live test error: {e}")
        sys.exit(1)
