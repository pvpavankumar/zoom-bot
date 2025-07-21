
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ZoomEventHandler:

    def __init__(self, bot_manager=None):
        self.bot_manager = bot_manager

        self.event_handlers = {
            "meeting.started": self._handle_meeting_started,
            "meeting.ended": self._handle_meeting_ended,
            "meeting.participant_joined": self._handle_participant_joined,
            "meeting.participant_left": self._handle_participant_left,
            "meeting.breakout_room_started": self._handle_breakout_room_started,
            "meeting.breakout_room_ended": self._handle_breakout_room_ended,
            "meeting.participant_joined_breakout_room": self._handle_participant_joined_breakout_room,
            "meeting.participant_left_breakout_room": self._handle_participant_left_breakout_room,
            "meeting.recording_started": self._handle_recording_started,
            "meeting.recording_stopped": self._handle_recording_stopped,
        }

    async def handle_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        try:
            logger.info(f"Handling Zoom event: {event_type}")

            if event_type in self.event_handlers:
                await self.event_handlers[event_type](payload)
                return True
            else:
                logger.warning(f"No handler for event type: {event_type}")
                return False

        except Exception as e:
            logger.error(f"Error handling event {event_type}: {e}")
            return False

    async def _handle_meeting_started(self, payload: Dict[str, Any]):
        meeting_id = payload.get("object", {}).get("id")
        topic = payload.get("object", {}).get("topic", "Unknown")

        logger.info(f"Meeting started: {topic} (ID: {meeting_id})")

        if self.bot_manager:
            pass

    async def _handle_meeting_ended(self, payload: Dict[str, Any]):
        meeting_id = payload.get("object", {}).get("id")

        logger.info(f"Meeting ended: {meeting_id}")

        if self.bot_manager:
            pass

    async def _handle_participant_joined(self, payload: Dict[str, Any]):
        participant = payload.get("object", {}).get("participant", {})
        user_name = participant.get("user_name", "Unknown")
        user_id = participant.get("user_id")

        logger.info(f"Participant joined meeting: {user_name}")

    async def _handle_participant_left(self, payload: Dict[str, Any]):
        participant = payload.get("object", {}).get("participant", {})
        user_name = participant.get("user_name", "Unknown")

        logger.info(f"Participant left meeting: {user_name}")

    async def _handle_breakout_room_started(self, payload: Dict[str, Any]):
        meeting_id = payload.get("object", {}).get("id")
        breakout_rooms = payload.get("object", {}).get("breakout_rooms", [])

        logger.info(f"Breakout rooms started for meeting {meeting_id}: {len(breakout_rooms)} rooms")

        if self.bot_manager:
            for room in breakout_rooms:
                room_data = {
                    "room_id": room.get("id"),
                    "room_name": room.get("name", f"Room {room.get('id')}"),
                    "meeting_id": meeting_id
                }

                await self.bot_manager.handle_room_created(room_data)

    async def _handle_breakout_room_ended(self, payload: Dict[str, Any]):
        meeting_id = payload.get("object", {}).get("id")
        breakout_rooms = payload.get("object", {}).get("breakout_rooms", [])

        logger.info(f"Breakout rooms ended for meeting {meeting_id}")

        if self.bot_manager:
            for room in breakout_rooms:
                room_data = {"room_id": room.get("id")}
                await self.bot_manager.handle_room_closed(room_data)

    async def _handle_participant_joined_breakout_room(self, payload: Dict[str, Any]):
        breakout_room = payload.get("object", {}).get("breakout_room", {})
        participant = payload.get("object", {}).get("participant", {})

        room_id = breakout_room.get("id")
        user_name = participant.get("user_name", "Unknown")

        logger.info(f"Participant {user_name} joined breakout room {room_id}")

        if self.bot_manager and room_id:
            await self.bot_manager.handle_participant_joined(room_id, participant)

    async def _handle_participant_left_breakout_room(self, payload: Dict[str, Any]):
        breakout_room = payload.get("object", {}).get("breakout_room", {})
        participant = payload.get("object", {}).get("participant", {})

        room_id = breakout_room.get("id")
        user_name = participant.get("user_name", "Unknown")

        logger.info(f"Participant {user_name} left breakout room {room_id}")

        if self.bot_manager and room_id:
            await self.bot_manager.handle_participant_left(room_id, participant)

    async def _handle_recording_started(self, payload: Dict[str, Any]):
        meeting_id = payload.get("object", {}).get("id")

        logger.info(f"Recording started for meeting {meeting_id}")

    async def _handle_recording_stopped(self, payload: Dict[str, Any]):
        meeting_id = payload.get("object", {}).get("id")

        logger.info(f"Recording stopped for meeting {meeting_id}")

    def get_supported_events(self) -> list:
        return list(self.event_handlers.keys())

    def add_custom_handler(self, event_type: str, handler):
        self.event_handlers[event_type] = handler
        logger.info(f"Added custom handler for event type: {event_type}")


async def process_webhook_event(event_type: str, payload: Dict[str, Any], bot_manager=None) -> bool:
    handler = ZoomEventHandler(bot_manager)
    return await handler.handle_event(event_type, payload)
