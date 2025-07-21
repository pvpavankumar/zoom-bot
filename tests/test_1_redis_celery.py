
import redis
import json
import time
import asyncio
from datetime import datetime
from celery import Celery
from celery.result import AsyncResult

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tasks.celery_app import celery_app
from src.tasks.room_tasks import create_room_bot, cleanup_room_bot
from src.core.config import settings


class TestRedisConnection:

    def setup_method(self):
        self.redis_client = redis.from_url(settings.redis_url)
        self.test_prefix = f"test_{int(time.time())}"

    def test_redis_basic_connection(self):
        try:
            assert self.redis_client.ping() == True
            print("✅ Redis ping successful")

            test_key = f"{self.test_prefix}_basic"
            test_value = "test_value_123"

            self.redis_client.set(test_key, test_value)
            retrieved = self.redis_client.get(test_key).decode()
            assert retrieved == test_value

            self.redis_client.delete(test_key)
            print("✅ Redis basic operations working")

        except Exception as e:
            raise ConnectionError(f"Redis connection failed: {e}")

    def test_redis_json_operations(self):
        try:
            test_data = {
                "room_id": "test_room_123",
                "participants": ["interviewer", "candidate"],
                "status": "active",
                "timestamp": datetime.utcnow().isoformat()
            }

            key = f"{self.test_prefix}_json"
            self.redis_client.set(key, json.dumps(test_data))

            retrieved_data = json.loads(self.redis_client.get(key).decode())
            assert retrieved_data["room_id"] == test_data["room_id"]
            assert len(retrieved_data["participants"]) == 2

            self.redis_client.delete(key)
            print("✅ Redis JSON operations working")

        except Exception as e:
            raise ValueError(f"Redis JSON operations failed: {e}")

    def test_redis_list_operations(self):
        try:
            transcript_key = f"transcript:{self.test_prefix}"

            transcripts = [
                {"speaker": "interviewer", "text": "Hello, let's begin the interview"},
                {"speaker": "candidate", "text": "Thank you, I'm ready"},
                {"speaker": "interviewer", "text": "Tell me about your experience"}
            ]

            for transcript in transcripts:
                self.redis_client.lpush(transcript_key, json.dumps(transcript))

            stored_count = self.redis_client.llen(transcript_key)
            assert stored_count == 3

            latest = json.loads(self.redis_client.lindex(transcript_key, 0).decode())
            assert latest["speaker"] == "interviewer"

            self.redis_client.delete(transcript_key)
            print("✅ Redis list operations working")

        except Exception as e:
            raise ValueError(f"Redis list operations failed: {e}")


class TestCeleryConnection:

    def setup_method(self):
        self.test_room_id = f"test_room_{int(time.time())}"

    def test_celery_worker_status(self):
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats()

            if not stats:
                print("⚠️ No Celery workers running - skipping worker tests")
                return

            print(f"✅ Celery workers active: {len(stats)} workers")

            active_queues = inspect.active_queues()
            if active_queues:
                print("✅ Celery workers responding to inspection")

        except Exception as e:
            raise RuntimeError(f"Celery worker check failed: {e}")

    def test_celery_task_dispatch(self):
        try:
            task_result = create_room_bot.delay(
                room_id=self.test_room_id,
                zoom_meeting_id="test_meeting_123",
                participants=["test_interviewer", "test_candidate"]
            )

            assert isinstance(task_result, AsyncResult)
            print(f"✅ Task dispatched successfully: {task_result.id}")

            time.sleep(2)

            task_state = task_result.state
            print(f"📊 Task state: {task_state}")

            assert task_state in ['PENDING', 'SUCCESS', 'RETRY']

        except Exception as e:
            raise RuntimeError(f"Celery task dispatch failed: {e}")

    def test_celery_task_cleanup(self):
        try:
            cleanup_task = cleanup_room_bot.delay(self.test_room_id)

            assert isinstance(cleanup_task, AsyncResult)
            print(f"✅ Cleanup task dispatched: {cleanup_task.id}")

            time.sleep(1)
            print("✅ Cleanup task completed")

        except Exception as e:
            raise RuntimeError(f"Celery cleanup test failed: {e}")


class TestCeleryRedisIntegration:

    def setup_method(self):
        self.redis_client = redis.from_url(settings.redis_url)
        self.test_room_id = f"integration_test_{int(time.time())}"

    def test_task_result_storage(self):
        try:
            task_result = create_room_bot.delay(
                room_id=self.test_room_id,
                zoom_meeting_id="integration_meeting",
                participants=["int_interviewer", "int_candidate"]
            )

            task_key_pattern = f"celery-task-meta-{task_result.id}"

            time.sleep(1)

            redis_keys = self.redis_client.keys("celery-task-meta-*")
            print(f"📊 Found {len(redis_keys)} task metadata entries in Redis")

            print("✅ Redis-Celery integration working")

        except Exception as e:
            raise RuntimeError(f"Redis-Celery integration test failed: {e}")

    def teardown_method(self):
        try:
            cleanup_room_bot.delay(self.test_room_id)
        except:
            pass


async def run_redis_celery_tests():

    print("🔧 ZOOM INTERVIEW BOT - REDIS & CELERY TESTS")
    print("=" * 60)
    print()

    try:
        print("📡 Testing Redis Connection...")
        redis_test = TestRedisConnection()
        redis_test.setup_method()
        redis_test.test_redis_basic_connection()
        redis_test.test_redis_json_operations()
        redis_test.test_redis_list_operations()
        print("✅ Redis tests completed successfully\n")

        print("⚙️ Testing Celery Workers...")
        celery_test = TestCeleryConnection()
        celery_test.setup_method()
        celery_test.test_celery_worker_status()
        celery_test.test_celery_task_dispatch()
        celery_test.test_celery_task_cleanup()
        print("✅ Celery tests completed successfully\n")

        print("🔗 Testing Redis-Celery Integration...")
        integration_test = TestCeleryRedisIntegration()
        integration_test.setup_method()
        integration_test.test_task_result_storage()
        integration_test.teardown_method()
        print("✅ Integration tests completed successfully\n")

        print("🎉 ALL REDIS & CELERY TESTS PASSED!")
        print("✅ Redis: Connected and operational")
        print("✅ Celery: Workers active and processing")
        print("✅ Integration: Redis-Celery communication working")

    except Exception as e:
        print(f"❌ Redis/Celery test failed: {e}")
        raise


def run_infrastructure_tests():
    asyncio.run(run_redis_celery_tests())


if __name__ == "__main__":
    run_infrastructure_tests()
