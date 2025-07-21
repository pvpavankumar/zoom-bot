
import asyncio
from typing import Dict, List, Optional, Any
import httpx

print("0000000000000")
from .auth import ZoomAuth
from ..utils.logging import get_logger
print("completed p1")
from ..core.config import settings

logger = get_logger(__name__)
print("1111111111111")


class ZoomClient:

    def __init__(self):
        print("2222222222222")
        self.auth = ZoomAuth()
        self.base_url = "https://api.zoom.us/v2"
        print("completed p2")
        self._session: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        print("3333333333333")
        self._session = httpx.AsyncClient(timeout=30.0)
        logger.info("Zoom client initialized")
        print("completed p3")

    async def cleanup(self):
        print("4444444444444")
        if self._session:
            await self._session.aclose()
            self._session = None
        logger.info("Zoom client cleaned up")

    async def get_meeting_info(self, meeting_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/meetings/{meeting_id}"

        headers = await self._get_auth_headers()

        async with self._session.get(url, headers=headers) as response:
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get meeting info: {response.status_code}")
                response.raise_for_status()

    async def list_meeting_participants(self, meeting_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/meetings/{meeting_id}/participants"

        headers = await self._get_auth_headers()

        async with self._session.get(url, headers=headers) as response:
            if response.status_code == 200:
                data = response.json()
                return data.get('participants', [])
            else:
                logger.error(f"Failed to list participants: {response.status_code}")
                return []

    async def get_breakout_rooms(self, meeting_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/meetings/{meeting_id}/breakout_rooms"

        headers = await self._get_auth_headers()

        async with self._session.get(url, headers=headers) as response:
            if response.status_code == 200:
                data = response.json()
                return data.get('breakout_rooms', [])
            else:
                logger.warning(f"Failed to get breakout rooms: {response.status_code}")
                return []

    async def join_meeting(self, meeting_id: str, participant_name: str = None) -> Dict[str, Any]:

        participant_name = participant_name or settings.bot_display_name

        logger.info(f"Joining meeting {meeting_id} as {participant_name}")

        await asyncio.sleep(2)

        return {
            "status": "joined",
            "meeting_id": meeting_id,
            "participant_name": participant_name,
            "participant_id": f"bot_{meeting_id}"
        }

    async def leave_meeting(self, meeting_id: str) -> Dict[str, Any]:
        logger.info(f"Leaving meeting {meeting_id}")

        await asyncio.sleep(1)

        return {
            "status": "left",
            "meeting_id": meeting_id
        }

    async def send_chat_message(self, meeting_id: str, message: str, to_participant: Optional[str] = None) -> bool:

        target = to_participant or "all participants"
        logger.info(f"Sending chat message to {target} in meeting {meeting_id}: {message[:50]}...")

        await asyncio.sleep(0.5)

        return True

    async def get_meeting_recording(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/meetings/{meeting_id}/recordings"

        headers = await self._get_auth_headers()

        async with self._session.get(url, headers=headers) as response:
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"No recording found for meeting {meeting_id}")
                return None

    async def create_webhook_subscription(self, event_types: List[str], endpoint_url: str) -> Dict[str, Any]:
        url = f"{self.base_url}/webhooks"

        headers = await self._get_auth_headers()

        payload = {
            "url": endpoint_url,
            "auth_user": "",
            "auth_password": "",
            "events": event_types
        }

        async with self._session.post(url, headers=headers, json=payload) as response:
            if response.status_code == 201:
                logger.info("Webhook subscription created successfully")
                return response.json()
            else:
                logger.error(f"Failed to create webhook: {response.status_code}")
                response.raise_for_status()

    async def update_participant_status(self, meeting_id: str, participant_id: str, action: str) -> bool:
        url = f"{self.base_url}/meetings/{meeting_id}/participants/{participant_id}/status"

        headers = await self._get_auth_headers()

        payload = {"action": action}

        async with self._session.patch(url, headers=headers, json=payload) as response:
            if response.status_code == 204:
                logger.debug(f"Updated participant {participant_id} status: {action}")
                return True
            else:
                logger.warning(f"Failed to update participant status: {response.status_code}")
                return False

    async def get_meeting_quality(self, meeting_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/metrics/meetings/{meeting_id}/participants/qos"

        headers = await self._get_auth_headers()

        async with self._session.get(url, headers=headers) as response:
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get meeting quality: {response.status_code}")
                return {}

    async def start_recording(self, meeting_id: str) -> bool:
        logger.info(f"Starting recording for meeting {meeting_id}")
        return True

    async def stop_recording(self, meeting_id: str) -> bool:
        logger.info(f"Stopping recording for meeting {meeting_id}")
        return True

    async def get_audio_stream(self, meeting_id: str, participant_id: str):
        logger.debug(f"Getting audio stream for participant {participant_id}")

        while True:
            yield b"dummy_audio_data"
            await asyncio.sleep(0.1)

    async def _get_auth_headers(self) -> Dict[str, str]:
        token = await self.auth.get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }


async def send_chat_message(room_id: str, message: str):
    logger.info(f"Sending message to room {room_id}: {message[:50]}...")

    await asyncio.sleep(0.1)


async def get_room_participants(room_id: str) -> List[Dict[str, Any]]:
    logger.debug(f"Getting participants for room {room_id}")

    return [
        {
            "user_id": "interviewer_123",
            "name": "Interviewer",
            "is_host": True,
            "is_speaking": False
        },
        {
            "user_id": "candidate_456",
            "name": "Candidate",
            "is_host": False,
            "is_speaking": True
        }
    ]


async def check_room_status(room_id: str) -> Dict[str, Any]:
    logger.debug(f"Checking status for room {room_id}")

    return {
        "room_id": room_id,
        "is_active": True,
        "participant_count": 2,
        "audio_active": True
    }
