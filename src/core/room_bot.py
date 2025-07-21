
import asyncio
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class Participant:
    user_id: str
    name: str
    role: str
    is_speaking: bool = False
    last_speech_time: Optional[datetime] = None
    audio_level: float = 0.0


@dataclass
class ConversationContext:
    messages: List[Dict] = field(default_factory=list)
    current_topic: Optional[str] = None
    interview_stage: str = "introduction"
    last_suggestion_time: Optional[datetime] = None
    participant_analysis: Dict[str, Dict] = field(default_factory=dict)


class RoomBot:

    def __init__(self, instance_id: str, room_id: str, room_name: str, meeting_id: str):
        self.instance_id = instance_id
        self.room_id = room_id
        self.room_name = room_name
        self.meeting_id = meeting_id

        self.is_active = False
        self.participants: Dict[str, Participant] = {}
        self.context = ConversationContext()
        self.audio_processor = None
        self.ai_analyzer = None
        self.chat_handler = None

        self.audio_processing_task: Optional[asyncio.Task] = None
        self.suggestion_task: Optional[asyncio.Task] = None
        self.chat_monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        logger.info("Initialized RoomBot %s for room %s", instance_id, room_name)

    async def start(self):
        logger.info("Starting RoomBot %s in room %s", self.instance_id, self.room_name)

        try:
            await self._initialize_components()

            await self._join_room()

            await self._start_processing_tasks()

            self.is_active = True
            logger.info("RoomBot %s started successfully", self.instance_id)

        except Exception as e:
            logger.error("Failed to start RoomBot %s: %s", self.instance_id, e)
            await self.stop()
            raise

    async def stop(self):
        logger.info("Stopping RoomBot %s", self.instance_id)

        self.is_active = False
        self._shutdown_event.set()

        await self._stop_processing_tasks()

        await self._leave_room()

        await self._cleanup_components()

        logger.info("RoomBot %s stopped", self.instance_id)

    async def handle_audio_data(self, audio_data: bytes, participant_id: str):
        if not self.is_active:
            return

        try:
            if self.audio_processor:
                await self.audio_processor.process_audio(audio_data, participant_id)

        except Exception as e:
            logger.error("Error processing audio from %s: %s", participant_id, e)

    async def handle_chat_message(self, message: str, sender_id: str) -> Optional[str]:
        if not self.is_active:
            return None

        try:
            if not self._is_bot_mentioned(message):
                return None

            if self.chat_handler:
                response = await self.chat_handler.handle_query(
                    message,
                    sender_id,
                    self.context
                )
                return response

        except Exception as e:
            logger.error("Error handling chat message: %s", e)
            return None

    async def handle_participant_joined(self, participant_data: dict):
        user_id = participant_data.get("user_id")
        name = participant_data.get("name", "Unknown")

        if user_id and user_id not in self.participants:
            role = await self._determine_participant_role(participant_data)

            participant = Participant(
                user_id=user_id,
                name=name,
                role=role
            )

            self.participants[user_id] = participant
            logger.info("Participant %s (%s) joined room %s", name, role, self.room_name)

            self.context.participant_analysis[user_id] = {
                "role": role,
                "join_time": datetime.utcnow().isoformat(),
                "speech_patterns": {}
            }

    async def handle_participant_left(self, participant_data: dict):
        user_id = participant_data.get("user_id")

        if user_id in self.participants:
            participant = self.participants[user_id]
            logger.info("Participant %s left room %s", participant.name, self.room_name)
            del self.participants[user_id]

            if not self.participants:
                logger.info("Room %s is now empty", self.room_name)
                await self.stop()

    async def get_status(self) -> dict:
        return {
            "instance_id": self.instance_id,
            "room_id": self.room_id,
            "room_name": self.room_name,
            "is_active": self.is_active,
            "participants": len(self.participants),
            "participant_details": [
                {
                    "name": p.name,
                    "role": p.role,
                    "is_speaking": p.is_speaking
                }
                for p in self.participants.values()
            ],
            "conversation_stage": self.context.interview_stage,
            "last_suggestion_time": self.context.last_suggestion_time.isoformat() if self.context.last_suggestion_time else None
        }

    async def _initialize_components(self):
        from ..audio import AudioProcessor
        from ..ai.analyzer import ConversationAnalyzer
        from ..ai.chat import ChatHandler

        self.audio_processor = AudioProcessor(self.instance_id)
        self.ai_analyzer = ConversationAnalyzer(self.instance_id)
        self.chat_handler = ChatHandler(self.instance_id)

        await self.audio_processor.initialize()
        await self.ai_analyzer.initialize()
        await self.chat_handler.initialize()

    async def _cleanup_components(self):
        if self.audio_processor:
            await self.audio_processor.cleanup()
        if self.ai_analyzer:
            await self.ai_analyzer.cleanup()
        if self.chat_handler:
            await self.chat_handler.cleanup()

    async def _join_room(self):
        logger.info("Joining room %s (hidden mode)", self.room_name)

        await asyncio.sleep(1)

    async def _leave_room(self):
        logger.info("Leaving room %s", self.room_name)

        await asyncio.sleep(0.5)

    async def _start_processing_tasks(self):
        self.audio_processing_task = asyncio.create_task(self._audio_processing_loop())
        self.suggestion_task = asyncio.create_task(self._suggestion_generation_loop())
        self.chat_monitoring_task = asyncio.create_task(self._chat_monitoring_loop())

    async def _stop_processing_tasks(self):
        tasks = [
            self.audio_processing_task,
            self.suggestion_task,
            self.chat_monitoring_task
        ]

        for task in tasks:
            if task and not task.done():
                task.cancel()

        await asyncio.gather(*[t for t in tasks if t], return_exceptions=True)

    async def _audio_processing_loop(self):
        while not self._shutdown_event.is_set():
            try:
                if self.audio_processor:
                    await self.audio_processor.process_pending_audio()

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error("Error in audio processing loop: %s", e)
                await asyncio.sleep(1)

    async def _suggestion_generation_loop(self):
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.utcnow()

                if self._should_generate_suggestion(current_time):
                    await self._generate_and_send_suggestion()
                    self.context.last_suggestion_time = current_time

                await asyncio.sleep(settings.suggestion_frequency)

            except Exception as e:
                logger.error("Error in suggestion generation loop: %s", e)
                await asyncio.sleep(5)

    async def _chat_monitoring_loop(self):
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(1)

            except Exception as e:
                logger.error("Error in chat monitoring loop: %s", e)
                await asyncio.sleep(2)

    async def _determine_participant_role(self, participant_data: dict) -> str:

        is_host = participant_data.get("is_host", False)
        is_co_host = participant_data.get("is_co_host", False)

        if is_host or is_co_host:
            return "interviewer"
        else:
            return "candidate"

    def _is_bot_mentioned(self, message: str) -> bool:
        bot_keywords = [
            settings.bot_name.lower(),
            settings.bot_display_name.lower(),
            "bot",
            "assistant",
            "help"
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in bot_keywords)

    def _should_generate_suggestion(self, current_time: datetime) -> bool:
        if not self.context.last_suggestion_time:
            return True

        time_since_last = (current_time - self.context.last_suggestion_time).total_seconds()
        return time_since_last >= settings.suggestion_frequency

    async def _generate_and_send_suggestion(self):
        if not self.ai_analyzer:
            return

        try:
            suggestion = await self.ai_analyzer.generate_suggestion(
                self.context,
                self.participants
            )

            if suggestion:
                await self._send_chat_message(suggestion)
                logger.info("Sent suggestion in room %s: %s", self.room_name, suggestion[:50])

        except Exception as e:
            logger.error("Error generating suggestion: %s", e)

    async def _send_chat_message(self, message: str):
        logger.debug("Sending chat message: %s", message)

        await asyncio.sleep(0.1)
