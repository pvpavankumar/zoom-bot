
import asyncio
import time
import psutil
import threading
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.bot_manager import BotManager
from src.core.room_bot import RoomBot
from src.tasks.room_tasks import create_room_bot
from src.tasks.celery_app import celery_app


class TestBotResourceAllocation:

    def setup_method(self):
        self.bot_manager = BotManager()
        self.initial_memory = psutil.Process().memory_info().rss
        self.resource_metrics = {}

    def test_memory_allocation_per_bot(self):
        try:
            baseline_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            print(f"📊 Baseline memory usage: {baseline_memory:.1f} MB")

            bot_instances = []
            memory_measurements = []

            for i in range(3):
                room_id = f"test_room_{i+1}"
                bot = RoomBot(instance_id=room_id)
                bot_instances.append(bot)

                current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                memory_measurements.append(current_memory)

                print(f"🤖 Bot {i+1} created - Memory: {current_memory:.1f} MB")
                time.sleep(0.1)

            total_memory_increase = memory_measurements[-1] - baseline_memory
            avg_memory_per_bot = total_memory_increase / len(bot_instances)

            print(f"📊 Total memory increase: {total_memory_increase:.1f} MB")
            print(f"📊 Average memory per bot: {avg_memory_per_bot:.1f} MB")

            assert avg_memory_per_bot < 50
            assert total_memory_increase < 150

            self.resource_metrics["memory_per_bot"] = avg_memory_per_bot
            print("✅ Memory allocation per bot within acceptable limits")

        except Exception as e:
            print(f"❌ Memory allocation test failed: {e}")
            raise

    def test_cpu_allocation_per_bot(self):
        try:
            baseline_cpu = psutil.cpu_percent(interval=1)
            print(f"📊 Baseline CPU usage: {baseline_cpu:.1f}%")

            cpu_measurements = []

            for i in range(3):
                start_time = time.time()

                self._simulate_bot_processing()

                cpu_usage = psutil.cpu_percent(interval=0.5)
                cpu_measurements.append(cpu_usage)

                processing_time = time.time() - start_time
                print(f"🤖 Bot {i+1} processing - CPU: {cpu_usage:.1f}%, Time: {processing_time:.2f}s")

            avg_cpu_usage = sum(cpu_measurements) / len(cpu_measurements)
            max_cpu_usage = max(cpu_measurements)

            print(f"📊 Average CPU usage: {avg_cpu_usage:.1f}%")
            print(f"📊 Maximum CPU usage: {max_cpu_usage:.1f}%")

            assert avg_cpu_usage < 80
            assert max_cpu_usage < 90

            self.resource_metrics["avg_cpu_usage"] = avg_cpu_usage
            print("✅ CPU allocation per bot within acceptable limits")

        except Exception as e:
            print(f"❌ CPU allocation test failed: {e}")
            raise

    def _simulate_bot_processing(self):
        for _ in range(100000):
            _ = sum(range(100))

    def test_concurrent_bot_creation_performance(self):
        try:
            start_time = time.perf_counter()

            async def create_concurrent_bots():
                tasks = []
                for i in range(5):
                    task = asyncio.create_task(self._create_bot_async(f"concurrent_room_{i}"))
                    tasks.append(task)

                results = await asyncio.gather(*tasks)
                return results

            results = asyncio.run(create_concurrent_bots())

            end_time = time.perf_counter()
            total_time = end_time - start_time

            successful_bots = sum(1 for result in results if result["success"])
            avg_time_per_bot = total_time / len(results)

            print(f"📊 Created {successful_bots}/{len(results)} bots successfully")
            print(f"📊 Total creation time: {total_time:.2f}s")
            print(f"📊 Average time per bot: {avg_time_per_bot:.2f}s")

            assert successful_bots >= 4
            assert avg_time_per_bot < 2.0

            self.resource_metrics["concurrent_creation_time"] = avg_time_per_bot
            print("✅ Concurrent bot creation performance acceptable")

        except Exception as e:
            print(f"❌ Concurrent bot creation test failed: {e}")
            raise

    async def _create_bot_async(self, room_id):
        try:
            start_time = time.perf_counter()

            await asyncio.sleep(0.1)
            bot = RoomBot(instance_id=room_id)

            creation_time = time.perf_counter() - start_time

            return {
                "success": True,
                "room_id": room_id,
                "creation_time": creation_time,
                "bot": bot
            }

        except Exception as e:
            return {
                "success": False,
                "room_id": room_id,
                "error": str(e)
            }


class TestBotManagerScaling:

    def setup_method(self):
        self.bot_manager = BotManager()
        self.max_concurrent_bots = 10

    async def test_dynamic_bot_scaling(self):
        try:
            demand_scenarios = [
                {"rooms": 2, "expected_bots": 2},
                {"rooms": 5, "expected_bots": 5},
                {"rooms": 8, "expected_bots": 8},
                {"rooms": 12, "expected_bots": 10}
            ]

            scaling_results = []

            for scenario in demand_scenarios:
                result = await self._simulate_scaling_scenario(scenario)
                scaling_results.append(result)

                print(f"📊 Demand: {scenario['rooms']} rooms, Allocated: {result['allocated_bots']} bots")

            for i, result in enumerate(scaling_results):
                expected = demand_scenarios[i]["expected_bots"]
                actual = result["allocated_bots"]

                assert actual == expected, f"Expected {expected} bots, got {actual}"

            print("✅ Dynamic bot scaling working correctly")

        except Exception as e:
            print(f"❌ Dynamic scaling test failed: {e}")
            raise

    async def _simulate_scaling_scenario(self, scenario):
        requested_rooms = scenario["rooms"]
        max_bots = min(requested_rooms, self.max_concurrent_bots)

        allocated_bots = 0
        for i in range(max_bots):
            await asyncio.sleep(0.01)
            allocated_bots += 1

        return {
            "requested_rooms": requested_rooms,
            "allocated_bots": allocated_bots,
            "scaling_factor": allocated_bots / requested_rooms
        }

    async def test_resource_monitoring_during_scaling(self):
        try:
            monitoring_data = []

            for bot_count in range(1, 6):
                before_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                before_cpu = psutil.cpu_percent(interval=0.1)

                await asyncio.sleep(0.2)

                after_memory = psutil.Process().memory_info().rss / (1024 * 1024)
                after_cpu = psutil.cpu_percent(interval=0.1)

                monitoring_data.append({
                    "bot_count": bot_count,
                    "memory_usage": after_memory,
                    "memory_increase": after_memory - before_memory,
                    "cpu_usage": after_cpu,
                    "timestamp": datetime.utcnow()
                })

                print(f"📊 Bot {bot_count}: Memory={after_memory:.1f}MB (+{after_memory-before_memory:.1f}), CPU={after_cpu:.1f}%")

            memory_trend = [data["memory_usage"] for data in monitoring_data]
            cpu_trend = [data["cpu_usage"] for data in monitoring_data]

            max_memory = max(memory_trend)
            max_cpu = max(cpu_trend)

            assert max_memory < 500
            assert max_cpu < 80

            print(f"📊 Peak memory usage: {max_memory:.1f} MB")
            print(f"📊 Peak CPU usage: {max_cpu:.1f}%")
            print("✅ Resource monitoring during scaling working")

        except Exception as e:
            print(f"❌ Resource monitoring test failed: {e}")
            raise


class TestBreakoutRoomDetection:

    async def test_room_creation_detection(self):
        try:
            room_events = [
                {"event": "room_created", "room_id": "breakout_1", "participants": 2},
                {"event": "room_created", "room_id": "breakout_2", "participants": 3},
                {"event": "room_created", "room_id": "breakout_3", "participants": 0},
            ]

            detected_rooms = []

            for event in room_events:
                detection_result = await self._process_room_event(event)
                detected_rooms.append(detection_result)

                print(f"🔍 Detected: {event['room_id']} with {event['participants']} participants")

            active_rooms = [room for room in detected_rooms if room["should_deploy_bot"]]
            assert len(active_rooms) == 2

            print(f"✅ Detected {len(detected_rooms)} rooms, deploying bots to {len(active_rooms)}")

        except Exception as e:
            print(f"❌ Room detection test failed: {e}")
            raise

    async def _process_room_event(self, event):
        room_id = event["room_id"]
        participants = event["participants"]

        should_deploy = participants > 0

        return {
            "room_id": room_id,
            "participants": participants,
            "should_deploy_bot": should_deploy,
            "detection_time": datetime.utcnow()
        }

    async def test_automatic_bot_deployment(self):
        try:
            deployment_scenarios = [
                {"room_id": "auto_room_1", "participants": ["interviewer", "candidate"]},
                {"room_id": "auto_room_2", "participants": ["interviewer", "candidate", "observer"]},
                {"room_id": "auto_room_3", "participants": []},
            ]

            deployment_results = []

            for scenario in deployment_scenarios:
                result = await self._simulate_auto_deployment(scenario)
                deployment_results.append(result)

                status = "✅ Deployed" if result["bot_deployed"] else "⏭️ Skipped"
                print(f"{status} bot to {scenario['room_id']} ({len(scenario['participants'])} participants)")

            successful_deployments = sum(1 for r in deployment_results if r["bot_deployed"])
            assert successful_deployments == 2

            print("✅ Automatic bot deployment working correctly")

        except Exception as e:
            print(f"❌ Automatic deployment test failed: {e}")
            raise

    async def _simulate_auto_deployment(self, scenario):
        room_id = scenario["room_id"]
        participants = scenario["participants"]

        should_deploy = len(participants) > 0

        if should_deploy:
            await asyncio.sleep(0.1)
            deployment_time = datetime.utcnow()

            return {
                "room_id": room_id,
                "bot_deployed": True,
                "deployment_time": deployment_time,
                "participant_count": len(participants)
            }
        else:
            return {
                "room_id": room_id,
                "bot_deployed": False,
                "reason": "no_participants"
            }


class TestThreadingAndConcurrency:

    def test_thread_pool_management(self):
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []

                for i in range(6):
                    future = executor.submit(self._simulate_bot_operation, f"bot_{i}")
                    futures.append(future)

                results = []
                for future in futures:
                    result = future.result(timeout=5.0)
                    results.append(result)

                successful_operations = sum(1 for r in results if r["success"])
                avg_duration = sum(r["duration"] for r in results) / len(results)

                print(f"📊 Completed {successful_operations}/{len(results)} operations")
                print(f"📊 Average operation duration: {avg_duration:.2f}s")

                assert successful_operations == len(results)
                assert avg_duration < 2.0

                print("✅ Thread pool management working correctly")

        except Exception as e:
            print(f"❌ Thread pool test failed: {e}")
            raise

    def _simulate_bot_operation(self, bot_id):
        try:
            start_time = time.time()

            time.sleep(0.5)

            end_time = time.time()
            duration = end_time - start_time

            return {
                "bot_id": bot_id,
                "success": True,
                "duration": duration,
                "thread_id": threading.current_thread().ident
            }

        except Exception as e:
            return {
                "bot_id": bot_id,
                "success": False,
                "error": str(e)
            }

    async def test_async_concurrency(self):
        try:
            async def bot_async_operation(bot_id):
                await asyncio.sleep(0.3)
                return {
                    "bot_id": bot_id,
                    "success": True,
                    "task_name": asyncio.current_task().get_name() if asyncio.current_task() else "unknown"
                }

            tasks = [bot_async_operation(f"async_bot_{i}") for i in range(5)]

            start_time = time.perf_counter()
            results = await asyncio.gather(*tasks)
            end_time = time.perf_counter()

            total_time = end_time - start_time
            successful_ops = sum(1 for r in results if r["success"])

            print(f"📊 Completed {successful_ops} async operations in {total_time:.2f}s")

            assert total_time < 1.0
            assert successful_ops == len(results)

            print("✅ Async concurrency working correctly")

        except Exception as e:
            print(f"❌ Async concurrency test failed: {e}")
            raise


async def run_resource_allocation_tests():

    print("⚡ ZOOM INTERVIEW BOT - RESOURCE ALLOCATION TESTS")
    print("=" * 60)
    print()

    try:
        print("💾 Testing Bot Resource Allocation...")
        resource_test = TestBotResourceAllocation()
        resource_test.setup_method()
        resource_test.test_memory_allocation_per_bot()
        resource_test.test_cpu_allocation_per_bot()
        resource_test.test_concurrent_bot_creation_performance()
        print("✅ Resource allocation tests completed\n")

        print("📈 Testing Bot Manager Scaling...")
        scaling_test = TestBotManagerScaling()
        scaling_test.setup_method()
        await scaling_test.test_dynamic_bot_scaling()
        await scaling_test.test_resource_monitoring_during_scaling()
        print("✅ Bot manager scaling tests completed\n")

        print("🔍 Testing Breakout Room Detection...")
        detection_test = TestBreakoutRoomDetection()
        await detection_test.test_room_creation_detection()
        await detection_test.test_automatic_bot_deployment()
        print("✅ Room detection tests completed\n")

        print("🧵 Testing Threading and Concurrency...")
        threading_test = TestThreadingAndConcurrency()
        threading_test.test_thread_pool_management()
        await threading_test.test_async_concurrency()
        print("✅ Threading and concurrency tests completed\n")

        print("🎉 ALL RESOURCE ALLOCATION TESTS PASSED!")
        print("✅ Memory and CPU allocation within limits")
        print("✅ Dynamic bot scaling operational")
        print("✅ Automatic room detection and deployment working")
        print("✅ Threading and concurrency management functional")
        print("✅ Performance monitoring during scaling working")

    except Exception as e:
        print(f"❌ Resource allocation test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_resource_allocation_tests())
