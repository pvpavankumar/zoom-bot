
import asyncio
import uuid
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

print("0000000000000")
from ..tasks.celery_app import celery_app
from ..tasks.room_tasks import create_room_bot, cleanup_room_bot
print("completed p1")
from ..zoom.client import ZoomClient
from ..utils.logging import get_logger
from .config import settings
print("1111111111111")

logger = get_logger(__name__)
print("completed p2")


@dataclass
class RoomInfo:
    room_id: str
    room_name: str
    meeting_id: str
    participants: List[str] = field(default_factory=list)
    bot_instance_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True


@dataclass
class BotInstance:
    instance_id: str
    room_id: str
    task_id: str
    worker_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    status: str = "initializing"


class BotManager:

    def __init__(self):
        self.zoom_client = ZoomClient()
        self.active_rooms: Dict[str, RoomInfo] = {}
        self.bot_instances: Dict[str, BotInstance] = {}
        self.monitoring_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        self._max_concurrent_rooms = settings.max_concurrent_rooms

    async def start(self):
        logger.info("Starting Bot Manager...")

        await self.zoom_client.initialize()

        monitor_task = asyncio.create_task(self._monitor_breakout_rooms())
        health_check_task = asyncio.create_task(self._health_check_loop())
        cleanup_task = asyncio.create_task(self._cleanup_loop())

        self.monitoring_tasks.update([monitor_task, health_check_task, cleanup_task])

        logger.info("Bot Manager started successfully")

    async def stop(self):
        logger.info("Stopping Bot Manager...")

        self._shutdown_event.set()

        await self._stop_all_bots()

        for task in self.monitoring_tasks:
            task.cancel()

        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        await self.zoom_client.cleanup()

        logger.info("Bot Manager stopped")

    async def handle_room_created(self, room_data: dict):
        room_id = room_data.get("room_id")
        room_name = room_data.get("room_name", f"Room {room_id}")
        meeting_id = room_data.get("meeting_id")

        if not room_id or not meeting_id:
            logger.error("Invalid room data received: %s", room_data)
            return

        if room_id in self.active_rooms:
            logger.warning("Room %s already exists", room_id)
            return

        if len(self.active_rooms) >= self._max_concurrent_rooms:
            logger.warning("Maximum concurrent rooms (%d) reached", self._max_concurrent_rooms)
            return

        logger.info("Creating bot for breakout room: %s", room_name)

        room_info = RoomInfo(
            room_id=room_id,
            room_name=room_name,
            meeting_id=meeting_id
        )

        await self._deploy_bot_to_room(room_info)

        self.active_rooms[room_id] = room_info

    async def handle_room_closed(self, room_data: dict):
        room_id = room_data.get("room_id")

        if not room_id or room_id not in self.active_rooms:
            logger.warning("Unknown room closure: %s", room_id)
            return

        logger.info("Handling room closure: %s", room_id)

        await self._stop_bot_for_room(room_id)

        if room_id in self.active_rooms:
            self.active_rooms[room_id].is_active = False
            del self.active_rooms[room_id]

    async def handle_participant_joined(self, room_id: str, participant_data: dict):
        if room_id not in self.active_rooms:
            return

        participant_id = participant_data.get("user_id")
        participant_name = participant_data.get("user_name")

        if participant_id:
            room_info = self.active_rooms[room_id]
            if participant_id not in room_info.participants:
                room_info.participants.append(participant_id)
                logger.info("Participant %s joined room %s", participant_name, room_id)

    async def handle_participant_left(self, room_id: str, participant_data: dict):
        if room_id not in self.active_rooms:
            return

        participant_id = participant_data.get("user_id")
        participant_name = participant_data.get("user_name")

        if participant_id:
            room_info = self.active_rooms[room_id]
            if participant_id in room_info.participants:
                room_info.participants.remove(participant_id)
                logger.info("Participant %s left room %s", participant_name, room_id)

                if not room_info.participants:
                    logger.info("Room %s is now empty, scheduling cleanup", room_id)
                    asyncio.create_task(self._delayed_room_cleanup(room_id))

    async def get_room_status(self, room_id: str) -> Optional[dict]:
        if room_id not in self.active_rooms:
            return None

        room_info = self.active_rooms[room_id]
        bot_instance = self.bot_instances.get(room_info.bot_instance_id)

        return {
            "room_id": room_id,
            "room_name": room_info.room_name,
            "participants": len(room_info.participants),
            "bot_status": bot_instance.status if bot_instance else "not_deployed",
            "created_at": room_info.created_at.isoformat(),
            "is_active": room_info.is_active
        }

    async def get_all_rooms_status(self) -> List[dict]:
        statuses = []
        for room_id in self.active_rooms:
            status = await self.get_room_status(room_id)
            if status:
                statuses.append(status)
        return statuses

    async def _deploy_bot_to_room(self, room_info: RoomInfo):
        try:
            instance_id = str(uuid.uuid4())

            task = create_room_bot.delay(
                instance_id=instance_id,
                room_id=room_info.room_id,
                room_name=room_info.room_name,
                meeting_id=room_info.meeting_id
            )

            bot_instance = BotInstance(
                instance_id=instance_id,
                room_id=room_info.room_id,
                task_id=task.id,
                status="initializing"
            )

            self.bot_instances[instance_id] = bot_instance
            room_info.bot_instance_id = instance_id

            logger.info("Deployed bot instance %s to room %s", instance_id, room_info.room_id)

        except Exception as e:
            logger.error("Failed to deploy bot to room %s: %s", room_info.room_id, e)

    async def _stop_bot_for_room(self, room_id: str):
        if room_id not in self.active_rooms:
            return

        room_info = self.active_rooms[room_id]
        if not room_info.bot_instance_id:
            return

        bot_instance = self.bot_instances.get(room_info.bot_instance_id)
        if not bot_instance:
            return

        try:
            bot_instance.status = "stopping"

            cleanup_room_bot.delay(
                instance_id=bot_instance.instance_id,
                room_id=room_id
            )

            del self.bot_instances[bot_instance.instance_id]
            room_info.bot_instance_id = None

            logger.info("Stopped bot instance %s for room %s", bot_instance.instance_id, room_id)

        except Exception as e:
            logger.error("Failed to stop bot for room %s: %s", room_id, e)

    async def _stop_all_bots(self):
        for room_id in list(self.active_rooms.keys()):
            await self._stop_bot_for_room(room_id)

    async def _monitor_breakout_rooms(self):
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(10)


            except Exception as e:
                logger.error("Error in breakout room monitoring: %s", e)
                await asyncio.sleep(5)

    async def _health_check_loop(self):
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.utcnow()

                for instance_id, bot_instance in list(self.bot_instances.items()):
                    time_since_heartbeat = (current_time - bot_instance.last_heartbeat).total_seconds()

                    if time_since_heartbeat > settings.health_check_interval * 2:
                        logger.warning("Bot instance %s appears to be dead", instance_id)
                        await self._handle_dead_bot_instance(instance_id)

                await asyncio.sleep(settings.health_check_interval)

            except Exception as e:
                logger.error("Error in health check loop: %s", e)
                await asyncio.sleep(5)

    async def _cleanup_loop(self):
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.utcnow()

                for room_id, room_info in list(self.active_rooms.items()):
                    if not room_info.is_active:
                        age = (current_time - room_info.created_at).total_seconds()
                        if age > 3600:
                            logger.info("Cleaning up old inactive room: %s", room_id)
                            del self.active_rooms[room_id]

                await asyncio.sleep(300)

            except Exception as e:
                logger.error("Error in cleanup loop: %s", e)
                await asyncio.sleep(30)

    async def _handle_dead_bot_instance(self, instance_id: str):
        if instance_id not in self.bot_instances:
            return

        bot_instance = self.bot_instances[instance_id]
        logger.warning("Handling dead bot instance %s for room %s", instance_id, bot_instance.room_id)

        del self.bot_instances[instance_id]

        if bot_instance.room_id in self.active_rooms:
            self.active_rooms[bot_instance.room_id].bot_instance_id = None

            room_info = self.active_rooms[bot_instance.room_id]
            if room_info.participants:
                logger.info("Redeploying bot to room %s", bot_instance.room_id)
                await self._deploy_bot_to_room(room_info)

    async def _delayed_room_cleanup(self, room_id: str, delay: int = 60):
        await asyncio.sleep(delay)

        if room_id in self.active_rooms:
            room_info = self.active_rooms[room_id]
            if not room_info.participants:
                logger.info("Cleaning up empty room: %s", room_id)
                await self._stop_bot_for_room(room_id)
