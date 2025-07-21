
import asyncio
import time
import sys
import os
from datetime import datetime
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from test_1_redis_celery import run_redis_celery_tests
from test_2_meeting_connection import run_meeting_connection_tests
from test_3_audio_monitoring import run_audio_monitoring_tests
from test_4_chat_response import run_chat_response_tests
from test_5_resource_allocation import run_resource_allocation_tests
from test_6_resource_cleanup import run_resource_cleanup_tests
from test_7_master_bot_threading import run_master_bot_threading_tests
from test_8_conversation_analysis import run_conversation_analysis_tests


class TestSuiteRunner:

    def __init__(self):
        self.test_modules = [
            {
                "name": "Redis & Celery Connection",
                "runner": run_redis_celery_tests,
                "description": "Tests Redis connectivity and Celery task processing"
            },
            {
                "name": "Meeting Connection",
                "runner": run_meeting_connection_tests,
                "description": "Tests Zoom API integration and breakout room connections"
            },
            {
                "name": "Audio Monitoring",
                "runner": run_audio_monitoring_tests,
                "description": "Tests multi-room audio capture and processing"
            },
            {
                "name": "Chat Response System",
                "runner": run_chat_response_tests,
                "description": "Tests interviewer chat and participant identification"
            },
            {
                "name": "Resource Allocation",
                "runner": run_resource_allocation_tests,
                "description": "Tests bot scaling and resource management"
            },
            {
                "name": "Resource Cleanup",
                "runner": run_resource_cleanup_tests,
                "description": "Tests bot cleanup and memory deallocation"
            },
            {
                "name": "Master Bot Threading",
                "runner": run_master_bot_threading_tests,
                "description": "Tests multi-threaded bot management"
            },
            {
                "name": "Conversation Analysis",
                "runner": run_conversation_analysis_tests,
                "description": "Tests participant recognition and interview assistance"
            }
        ]

        self.results = []
        self.start_time = None
        self.total_duration = 0

    async def run_all_tests(self):

        print("🚀 ZOOM INTERVIEW BOT - COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🧪 Total test modules: {len(self.test_modules)}")
        print()

        self.start_time = time.time()

        for i, test_module in enumerate(self.test_modules, 1):
            await self._run_single_test_module(i, test_module)
            print()

        self.total_duration = time.time() - self.start_time
        await self._generate_final_report()

    async def _run_single_test_module(self, module_number, test_module):

        print(f"🧪 TEST MODULE {module_number}/{len(self.test_modules)}: {test_module['name']}")
        print(f"📝 {test_module['description']}")
        print("-" * 50)

        module_start_time = time.time()

        try:
            await test_module["runner"]()

            module_duration = time.time() - module_start_time

            self.results.append({
                "module": test_module["name"],
                "status": "PASSED",
                "duration": module_duration,
                "error": None
            })

            print(f"✅ {test_module['name']} COMPLETED in {module_duration:.2f}s")

        except Exception as e:
            module_duration = time.time() - module_start_time

            self.results.append({
                "module": test_module["name"],
                "status": "FAILED",
                "duration": module_duration,
                "error": str(e),
                "traceback": traceback.format_exc()
            })

            print(f"❌ {test_module['name']} FAILED in {module_duration:.2f}s")
            print(f"💥 Error: {str(e)}")


    async def _generate_final_report(self):

        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)

        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASSED"])
        failed_tests = len([r for r in self.results if r["status"] == "FAILED"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"🕒 Total Duration: {self.total_duration:.2f} seconds")
        print(f"🧪 Total Test Modules: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()

        print("📋 INDIVIDUAL MODULE RESULTS:")
        print("-" * 50)

        for i, result in enumerate(self.results, 1):
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{i:2d}. {status_icon} {result['module']:<35} {result['duration']:>6.2f}s")

            if result["error"]:
                print(f"    💥 Error: {result['error']}")

        print()

        if failed_tests > 0:
            print("🔍 FAILED TEST DETAILS:")
            print("-" * 50)

            for result in self.results:
                if result["status"] == "FAILED":
                    print(f"❌ {result['module']}")
                    print(f"   Error: {result['error']}")
                    print()

        print("⚡ PERFORMANCE ANALYSIS:")
        print("-" * 50)

        if self.results:
            durations = [r["duration"] for r in self.results]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)

            slowest_test = max(self.results, key=lambda x: x["duration"])
            fastest_test = min(self.results, key=lambda x: x["duration"])

            print(f"⏱️  Average module time: {avg_duration:.2f}s")
            print(f"🐌 Slowest module: {slowest_test['module']} ({max_duration:.2f}s)")
            print(f"⚡ Fastest module: {fastest_test['module']} ({min_duration:.2f}s)")

        print()

        if passed_tests > 0:
            print("🎯 VERIFIED SYSTEM CAPABILITIES:")
            print("-" * 50)

            capabilities = [
                ("Redis & Celery", "Distributed task processing"),
                ("Zoom Integration", "Meeting and breakout room connectivity"),
                ("Audio Processing", "Multi-room audio monitoring"),
                ("AI Chat System", "Interviewer assistance and guidance"),
                ("Resource Management", "Dynamic bot scaling and allocation"),
                ("Cleanup System", "Proper resource deallocation"),
                ("Threading", "Multi-threaded bot management"),
                ("AI Analysis", "Conversation analysis and participant recognition")
            ]

            for i, (capability, description) in enumerate(capabilities):
                if i < len(self.results) and self.results[i]["status"] == "PASSED":
                    print(f"✅ {capability:<20} - {description}")
                else:
                    print(f"❌ {capability:<20} - {description}")

        print()

        if success_rate >= 100:
            print("🎉 ALL TESTS PASSED! Zoom Interview Bot is fully operational.")
            print("🚀 System ready for production deployment.")
        elif success_rate >= 75:
            print("⚠️  Most tests passed. Review failed modules before deployment.")
            print("🔧 Some functionality may need attention.")
        else:
            print("❌ Multiple test failures detected. System requires attention.")
            print("🛠️  Please fix failed modules before deployment.")

        print()
        print("📝 Test report completed at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    async def run_specific_test(self, test_number):

        if 1 <= test_number <= len(self.test_modules):
            test_module = self.test_modules[test_number - 1]

            print(f"🎯 RUNNING SPECIFIC TEST: {test_module['name']}")
            print("=" * 50)

            await self._run_single_test_module(test_number, test_module)

            result = self.results[-1] if self.results else None
            if result:
                print()
                print("📊 RESULT:")
                status_icon = "✅" if result["status"] == "PASSED" else "❌"
                print(f"{status_icon} {result['module']}: {result['status']} in {result['duration']:.2f}s")

                if result["error"]:
                    print(f"💥 Error: {result['error']}")
        else:
            print(f"❌ Invalid test number. Please choose 1-{len(self.test_modules)}")

    def list_available_tests(self):

        print("📋 AVAILABLE TEST MODULES:")
        print("=" * 50)

        for i, test_module in enumerate(self.test_modules, 1):
            print(f"{i}. {test_module['name']}")
            print(f"   {test_module['description']}")
            print()


async def run_startup_tests():

    print("🧪 RUNNING STARTUP VALIDATION TESTS")
    print("=" * 50)

    runner = TestSuiteRunner()
    await runner.run_all_tests()

    passed_tests = len([r for r in runner.results if r["status"] == "PASSED"])
    total_tests = len(runner.results)

    success = passed_tests == total_tests

    if success:
        print("✅ ALL STARTUP TESTS PASSED - Bot ready to start!")
    else:
        print(f"❌ {total_tests - passed_tests} tests failed - Bot may have issues")

    return success


async def main():

    runner = TestSuiteRunner()

    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            runner.list_available_tests()
            return

        try:
            test_number = int(sys.argv[1])
            await runner.run_specific_test(test_number)
            return
        except ValueError:
            print("❌ Invalid argument. Use 'list' or a test number (1-8)")
            return

    await runner.run_all_tests()


if __name__ == "__main__":
    print("🧪 Zoom Interview Bot Test Suite")
    print("Usage:")
    print("  python run_all_tests.py       - Run all tests")
    print("  python run_all_tests.py list  - List available tests")
    print("  python run_all_tests.py 3     - Run specific test (1-8)")
    print()

    asyncio.run(main())
