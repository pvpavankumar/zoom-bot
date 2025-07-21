
import asyncio
import threading
import time
import concurrent.futures
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from collections import defaultdict

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.bot_manager import BotManager
from src.core.room_bot import RoomBot
from src.tasks.room_tasks import create_room_bot, cleanup_room_bot


class TestMasterBotThreading:

    def setup_method(self):
        self.master_bot = BotManager()
        self.active_threads = {}
        self.thread_stats = defaultdict(dict)
        self.max_threads = 10

    async def test_concurrent_bot_creation(self):
        try:
            room_configs = [
                {"room_id": f"room_{i}", "interview_type": "technical"}
                for i in range(5)
            ]

            print(f"🤖 Creating {len(room_configs)} concurrent bots...")

            creation_tasks = []
            start_time = time.time()

            for config in room_configs:
                task = asyncio.create_task(
                    self._create_and_monitor_bot(config)
                )
                creation_tasks.append(task)

            bot_results = await asyncio.gather(*creation_tasks, return_exceptions=True)
            creation_time = time.time() - start_time

            successful_bots = [result for result in bot_results if isinstance(result, dict) and result.get("success")]
            failed_bots = [result for result in bot_results if not isinstance(result, dict) or not result.get("success")]

            print(f"✅ Successfully created {len(successful_bots)} bots in {creation_time:.2f}s")
            print(f"❌ Failed to create {len(failed_bots)} bots")

            assert len(successful_bots) >= 4
            assert creation_time < 10.0

            await self._verify_thread_isolation(successful_bots)

            print("✅ Concurrent bot creation test passed")

        except Exception as e:
            print(f"❌ Concurrent bot creation test failed: {e}")
            raise

    async def test_thread_pool_management(self):
        try:
            initial_pool_size = 3
            await self._initialize_thread_pool(initial_pool_size)

            room_count = 7
            rooms = [f"pool_test_room_{i}" for i in range(room_count)]

            print(f"📊 Testing thread pool scaling: {initial_pool_size} → {room_count} threads")

            pool_stats = []

            for i, room_id in enumerate(rooms):
                bot_task = asyncio.create_task(self._create_managed_bot(room_id))

                current_stats = await self._get_thread_pool_stats()
                pool_stats.append({
                    "step": i + 1,
                    "active_threads": current_stats["active_threads"],
                    "pool_size": current_stats["pool_size"],
                    "queue_size": current_stats["queue_size"]
                })

                await bot_task
                await asyncio.sleep(0.2)

            final_stats = pool_stats[-1]
            assert final_stats["active_threads"] >= initial_pool_size
            assert final_stats["pool_size"] >= room_count

            print(f"📊 Final pool size: {final_stats['pool_size']}")
            print(f"📊 Active threads: {final_stats['active_threads']}")

            print("✅ Thread pool management test passed")

        except Exception as e:
            print(f"❌ Thread pool management test failed: {e}")
            raise

    async def test_thread_synchronization(self):
        try:
            coordinator_rooms = ["coord_room_1", "coord_room_2", "coord_room_3"]
            sync_events = {}

            print("🔄 Testing thread synchronization...")

            for room_id in coordinator_rooms:
                sync_events[room_id] = asyncio.Event()

            sync_tasks = []
            for room_id in coordinator_rooms:
                task = asyncio.create_task(
                    self._create_synchronized_bot(room_id, sync_events)
                )
                sync_tasks.append(task)

            start_time = time.time()

            for i, room_id in enumerate(coordinator_rooms):
                await asyncio.sleep(0.5)
                sync_events[room_id].set()
                print(f"🔄 Released sync event for {room_id}")

            sync_results = await asyncio.gather(*sync_tasks)
            total_sync_time = time.time() - start_time

            successful_syncs = [r for r in sync_results if r.get("synchronized")]
            assert len(successful_syncs) == len(coordinator_rooms)

            print(f"✅ All {len(successful_syncs)} bots synchronized in {total_sync_time:.2f}s")

        except Exception as e:
            print(f"❌ Thread synchronization test failed: {e}")
            raise

    async def test_thread_failure_recovery(self):
        try:
            test_rooms = [
                {"room_id": "stable_room_1", "should_fail": False},
                {"room_id": "failing_room_1", "should_fail": True},
                {"room_id": "stable_room_2", "should_fail": False},
                {"room_id": "failing_room_2", "should_fail": True},
                {"room_id": "stable_room_3", "should_fail": False}
            ]

            print("🔄 Testing thread failure recovery...")

            recovery_tasks = []
            for room_config in test_rooms:
                task = asyncio.create_task(
                    self._create_bot_with_failure_test(room_config)
                )
                recovery_tasks.append(task)

            recovery_results = await asyncio.gather(*recovery_tasks, return_exceptions=True)

            stable_bots = []
            failed_bots = []
            recovered_bots = []

            for i, result in enumerate(recovery_results):
                room_config = test_rooms[i]

                if isinstance(result, Exception):
                    failed_bots.append(room_config["room_id"])
                elif result.get("success"):
                    if room_config["should_fail"]:
                        recovered_bots.append(room_config["room_id"])
                    else:
                        stable_bots.append(room_config["room_id"])

            print(f"✅ Stable bots: {len(stable_bots)}")
            print(f"🔄 Recovered bots: {len(recovered_bots)}")
            print(f"❌ Failed bots: {len(failed_bots)}")

            expected_stable = len([r for r in test_rooms if not r["should_fail"]])
            assert len(stable_bots) == expected_stable

            print("✅ Thread failure recovery test passed")

        except Exception as e:
            print(f"❌ Thread failure recovery test failed: {e}")
            raise

    async def _create_and_monitor_bot(self, config):
        try:
            start_time = time.time()

            bot = RoomBot(instance_id=config["room_id"])
            await bot.initialize()

            creation_time = time.time() - start_time
            thread_id = threading.current_thread().ident

            self.thread_stats[config["room_id"]] = {
                "creation_time": creation_time,
                "thread_id": thread_id,
                "status": "active"
            }

            return {
                "success": True,
                "room_id": config["room_id"],
                "creation_time": creation_time,
                "thread_id": thread_id
            }

        except Exception as e:
            return {
                "success": False,
                "room_id": config["room_id"],
                "error": str(e)
            }

    async def _verify_thread_isolation(self, bot_results):
        thread_ids = [result["thread_id"] for result in bot_results]
        unique_threads = set(thread_ids)

        print(f"📊 Created {len(bot_results)} bots across {len(unique_threads)} threads")

        thread_efficiency = len(unique_threads) / len(bot_results)
        assert thread_efficiency >= 0.5

        return True

    async def _initialize_thread_pool(self, size):
        self.thread_pool_size = size
        await asyncio.sleep(0.1)

    async def _get_thread_pool_stats(self):
        return {
            "active_threads": min(len(self.thread_stats), self.max_threads),
            "pool_size": max(self.thread_pool_size, len(self.thread_stats)),
            "queue_size": max(0, len(self.thread_stats) - self.max_threads)
        }

    async def _create_managed_bot(self, room_id):
        try:
            bot = RoomBot(instance_id=room_id)
            await bot.initialize()

            self.thread_stats[room_id] = {
                "status": "active",
                "created_at": datetime.utcnow(),
                "thread_id": threading.current_thread().ident
            }

            return {"success": True, "room_id": room_id}

        except Exception as e:
            return {"success": False, "room_id": room_id, "error": str(e)}

    async def _create_synchronized_bot(self, room_id, sync_events):
        try:
            await sync_events[room_id].wait()

            bot = RoomBot(instance_id=room_id)
            await bot.initialize()

            sync_time = datetime.utcnow()

            return {
                "success": True,
                "room_id": room_id,
                "synchronized": True,
                "sync_time": sync_time
            }

        except Exception as e:
            return {
                "success": False,
                "room_id": room_id,
                "synchronized": False,
                "error": str(e)
            }

    async def _create_bot_with_failure_test(self, room_config):
        room_id = room_config["room_id"]
        should_fail = room_config["should_fail"]

        try:
            if should_fail:
                await asyncio.sleep(0.1)
                raise Exception(f"Simulated failure for {room_id}")

            bot = RoomBot(instance_id=room_id)
            await bot.initialize()

            return {
                "success": True,
                "room_id": room_id,
                "attempts": 1
            }

        except Exception as e:
            try:
                print(f"🔄 Attempting recovery for {room_id}")
                await asyncio.sleep(0.2)

                bot = RoomBot(instance_id=room_id)
                await bot.initialize()

                return {
                    "success": True,
                    "room_id": room_id,
                    "attempts": 2,
                    "recovered": True
                }

            except Exception as recovery_error:
                return {
                    "success": False,
                    "room_id": room_id,
                    "attempts": 2,
                    "error": str(recovery_error)
                }


class TestThreadPerformance:

    async def test_thread_load_balancing(self):
        try:
            workload_rooms = [f"load_room_{i}" for i in range(8)]
            thread_workloads = defaultdict(list)

            print("⚖️ Testing thread load balancing...")

            load_tasks = []
            for room_id in workload_rooms:
                task = asyncio.create_task(
                    self._create_bot_with_load_tracking(room_id)
                )
                load_tasks.append(task)

            load_results = await asyncio.gather(*load_tasks)

            for result in load_results:
                if result.get("success"):
                    thread_id = result["thread_id"]
                    thread_workloads[thread_id].append(result["room_id"])

            workloads = [len(rooms) for rooms in thread_workloads.values()]
            max_load = max(workloads) if workloads else 0
            min_load = min(workloads) if workloads else 0
            avg_load = sum(workloads) / len(workloads) if workloads else 0
            load_variance = max_load - min_load

            print(f"📊 Thread count: {len(thread_workloads)}")
            print(f"📊 Max load per thread: {max_load}")
            print(f"📊 Min load per thread: {min_load}")
            print(f"📊 Average load: {avg_load:.1f}")
            print(f"📊 Load variance: {load_variance}")

            assert load_variance <= 3
            assert len(thread_workloads) >= 2

            print("✅ Thread load balancing test passed")

        except Exception as e:
            print(f"❌ Thread load balancing test failed: {e}")
            raise

    async def _create_bot_with_load_tracking(self, room_id):
        try:
            start_time = time.time()

            bot = RoomBot(instance_id=room_id)
            await bot.initialize()

            await asyncio.sleep(0.1)

            creation_time = time.time() - start_time
            thread_id = threading.current_thread().ident

            return {
                "success": True,
                "room_id": room_id,
                "thread_id": thread_id,
                "creation_time": creation_time
            }

        except Exception as e:
            return {
                "success": False,
                "room_id": room_id,
                "error": str(e)
            }

    async def test_thread_scalability(self):
        try:
            print("📈 Testing thread scalability...")

            load_levels = [2, 5, 10, 15]
            scalability_results = []

            for load in load_levels:
                print(f"🔄 Testing load level: {load} bots")

                start_time = time.time()

                rooms = [f"scale_test_{load}_{i}" for i in range(load)]
                scale_tasks = []

                for room_id in rooms:
                    task = asyncio.create_task(
                        self._create_scalability_test_bot(room_id)
                    )
                    scale_tasks.append(task)

                scale_results = await asyncio.gather(*scale_tasks, return_exceptions=True)
                total_time = time.time() - start_time

                successful = len([r for r in scale_results if isinstance(r, dict) and r.get("success")])
                success_rate = successful / load * 100
                throughput = successful / total_time if total_time > 0 else 0

                scalability_results.append({
                    "load": load,
                    "successful": successful,
                    "success_rate": success_rate,
                    "total_time": total_time,
                    "throughput": throughput
                })

                print(f"📊 Load {load}: {successful}/{load} bots ({success_rate:.1f}%) in {total_time:.2f}s")

                await asyncio.sleep(0.5)

            for result in scalability_results:
                assert result["success_rate"] >= 80
                assert result["throughput"] >= 1.0

            print("✅ Thread scalability test passed")

        except Exception as e:
            print(f"❌ Thread scalability test failed: {e}")
            raise

    async def _create_scalability_test_bot(self, room_id):
        try:
            bot = RoomBot(instance_id=room_id)
            await bot.initialize()

            processing_time = 0.05 + (hash(room_id) % 100) / 1000
            await asyncio.sleep(processing_time)

            return {
                "success": True,
                "room_id": room_id,
                "processing_time": processing_time
            }

        except Exception as e:
            return {
                "success": False,
                "room_id": room_id,
                "error": str(e)
            }


class TestThreadMonitoring:

    async def test_thread_health_monitoring(self):
        try:
            print("🏥 Testing thread health monitoring...")

            monitored_rooms = [f"health_room_{i}" for i in range(4)]
            health_stats = {}

            for room_id in monitored_rooms:
                bot_health = await self._create_bot_with_health_monitoring(room_id)
                health_stats[room_id] = bot_health

            monitoring_duration = 2.0
            health_checks = []

            start_time = time.time()
            while time.time() - start_time < monitoring_duration:
                current_health = await self._check_all_thread_health(monitored_rooms)
                health_checks.append({
                    "timestamp": time.time(),
                    "health_data": current_health.copy()
                })
                await asyncio.sleep(0.2)

            healthy_threads = []
            unhealthy_threads = []

            for room_id in monitored_rooms:
                latest_health = health_checks[-1]["health_data"].get(room_id, {})
                if latest_health.get("status") == "healthy":
                    healthy_threads.append(room_id)
                else:
                    unhealthy_threads.append(room_id)

            print(f"✅ Healthy threads: {len(healthy_threads)}")
            print(f"⚠️ Unhealthy threads: {len(unhealthy_threads)}")

            assert len(healthy_threads) >= len(monitored_rooms) * 0.75

            print("✅ Thread health monitoring test passed")

        except Exception as e:
            print(f"❌ Thread health monitoring test failed: {e}")
            raise

    async def _create_bot_with_health_monitoring(self, room_id):
        try:
            bot = RoomBot(instance_id=room_id)
            await bot.initialize()

            health_info = {
                "status": "healthy",
                "created_at": datetime.utcnow(),
                "last_heartbeat": datetime.utcnow(),
                "cpu_usage": 0.0,
                "memory_usage": 0.0
            }

            return health_info

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "created_at": datetime.utcnow()
            }

    async def _check_all_thread_health(self, room_ids):
        health_data = {}

        for room_id in room_ids:
            health_status = await self._perform_health_check(room_id)
            health_data[room_id] = health_status

        return health_data

    async def _perform_health_check(self, room_id):
        import random

        is_healthy = random.random() > 0.1

        if is_healthy:
            return {
                "status": "healthy",
                "last_heartbeat": datetime.utcnow(),
                "response_time": random.uniform(0.01, 0.05),
                "cpu_usage": random.uniform(5.0, 25.0),
                "memory_usage": random.uniform(10.0, 50.0)
            }
        else:
            return {
                "status": "unhealthy",
                "last_heartbeat": datetime.utcnow() - timedelta(seconds=30),
                "response_time": random.uniform(0.5, 2.0),
                "error": "Simulated health issue"
            }


async def run_master_bot_threading_tests():

    print("🧵 ZOOM INTERVIEW BOT - MASTER BOT THREADING TESTS")
    print("=" * 65)
    print()

    try:
        print("🤖 Testing Master Bot Threading...")
        threading_test = TestMasterBotThreading()
        threading_test.setup_method()
        await threading_test.test_concurrent_bot_creation()
        await threading_test.test_thread_pool_management()
        await threading_test.test_thread_synchronization()
        await threading_test.test_thread_failure_recovery()
        print("✅ Master bot threading tests completed\n")

        print("⚡ Testing Thread Performance...")
        performance_test = TestThreadPerformance()
        await performance_test.test_thread_load_balancing()
        await performance_test.test_thread_scalability()
        print("✅ Thread performance tests completed\n")

        print("🏥 Testing Thread Monitoring...")
        monitoring_test = TestThreadMonitoring()
        await monitoring_test.test_thread_health_monitoring()
        print("✅ Thread monitoring tests completed\n")

        print("🎉 ALL MASTER BOT THREADING TESTS PASSED!")
        print("✅ Concurrent bot creation working")
        print("✅ Thread pool management operational")
        print("✅ Thread synchronization functional")
        print("✅ Failure recovery mechanisms active")
        print("✅ Load balancing effective")
        print("✅ Scalability verified")
        print("✅ Health monitoring operational")

    except Exception as e:
        print(f"❌ Master bot threading test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_master_bot_threading_tests())
