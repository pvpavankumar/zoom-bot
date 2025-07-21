
import time
import jwt
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..core.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ZoomAuth:

    def __init__(self):
        self.api_key = settings.zoom_api_key
        self.api_secret = settings.zoom_api_secret
        self.sdk_key = settings.zoom_sdk_key
        self.sdk_secret = settings.zoom_sdk_secret

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._refresh_token: Optional[str] = None

    async def get_access_token(self) -> str:
        if self._is_token_valid():
            return self._access_token

        await self._refresh_access_token()
        return self._access_token

    def generate_jwt_token(self, expires_in: int = 3600) -> str:
        now = int(time.time())
        payload = {
            'iss': self.sdk_key,
            'exp': now + expires_in,
            'iat': now,
            'aud': 'zoom',
            'app_key': self.sdk_key,
            'alg': 'HS256'
        }

        token = jwt.encode(payload, self.sdk_secret, algorithm='HS256')
        logger.debug("Generated JWT token for Zoom SDK")
        return token

    async def authenticate_oauth(self, authorization_code: str, redirect_uri: str) -> Dict[str, Any]:
        token_url = "https://zoom.us/oauth/token"

        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        auth = (self.api_key, self.api_secret)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers=headers,
                auth=auth
            )

            if response.status_code == 200:
                token_data = response.json()
                self._store_tokens(token_data)
                logger.info("Successfully authenticated with Zoom OAuth")
                return token_data
            else:
                logger.error(f"OAuth authentication failed: {response.status_code} - {response.text}")
                raise Exception(f"OAuth authentication failed: {response.status_code}")

    async def refresh_token(self) -> Dict[str, Any]:
        if not self._refresh_token:
            raise Exception("No refresh token available")

        token_url = "https://zoom.us/oauth/token"

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self._refresh_token
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        auth = (self.api_key, self.api_secret)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers=headers,
                auth=auth
            )

            if response.status_code == 200:
                token_data = response.json()
                self._store_tokens(token_data)
                logger.info("Successfully refreshed Zoom access token")
                return token_data
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                raise Exception(f"Token refresh failed: {response.status_code}")

    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        base_url = "https://zoom.us/oauth/authorize"
        params = {
            'response_type': 'code',
            'client_id': self.api_key,
            'redirect_uri': redirect_uri
        }

        if state:
            params['state'] = state

        scopes = [
            'meeting:read',
            'meeting:write',
            'webinar:read',
            'webinar:write',
            'user:read',
            'chat_message:write',
            'chat_channel:read'
        ]
        params['scope'] = ' '.join(scopes)

        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{base_url}?{query_string}"

    async def validate_webhook_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        webhook_secret = settings.zoom_webhook_secret

        if not webhook_secret:
            logger.warning("No webhook secret configured")
            return False

        import hmac
        import hashlib

        message = f"v0:{timestamp}:{payload}"
        expected_signature = hmac.new(
            webhook_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        expected_signature = f"v0={expected_signature}"

        return hmac.compare_digest(expected_signature, signature)

    def _is_token_valid(self) -> bool:
        if not self._access_token or not self._token_expires_at:
            return False

        buffer_time = timedelta(minutes=5)
        return datetime.utcnow() < (self._token_expires_at - buffer_time)

    async def _refresh_access_token(self):
        if self._refresh_token:
            try:
                await self.refresh_token()
                return
            except Exception as e:
                logger.warning(f"Failed to refresh token: {e}")

        logger.error("Unable to refresh access token - re-authentication required")
        raise Exception("Access token expired and refresh failed")

    def _store_tokens(self, token_data: Dict[str, Any]):
        self._access_token = token_data.get('access_token')
        self._refresh_token = token_data.get('refresh_token')

        expires_in = token_data.get('expires_in', 3600)
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        logger.debug(f"Stored tokens, expires at: {self._token_expires_at}")

    def get_auth_headers(self) -> Dict[str, str]:
        if not self._access_token:
            raise Exception("No access token available")

        return {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }
