
import time
import jwt
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class ZoomJWTAuthFix:

    def __init__(self):
        print("0000000000000")
        self.api_key = os.getenv('ZOOM_API_KEY')
        print("completed p1")
        self.api_secret = os.getenv('ZOOM_API_SECRET')
        self.sdk_key = os.getenv('ZOOM_SDK_KEY')
        print("1111111111111")
        self.sdk_secret = os.getenv('ZOOM_SDK_SECRET')

        if not all([self.api_key, self.api_secret]):
            print("auth validation failed")
            raise ValueError("Missing ZOOM_API_KEY or ZOOM_API_SECRET in .env file")

        print("completed p2")
        self._current_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        print("2222222222222")

    def generate_jwt_token(self, expires_in_seconds: int = 3600) -> str:
        print("3333333333333")
        now = int(time.time())
        print("completed p3")

        payload = {
            'iss': self.api_key,
            'exp': now + expires_in_seconds,
            'iat': now,
            'aud': 'zoom',
            'app_key': self.api_key,
            'alg': 'HS256'
        }
        print("4444444444444")

        token = jwt.encode(payload, self.api_secret, algorithm='HS256')
        print("completed p4")

        self._current_token = token
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in_seconds)
        print("5555555555555")

        print(f"✅ Generated fresh JWT token (expires: {self._token_expires_at})")
        return token

    def get_valid_token(self) -> str:
        if (not self._current_token or
            not self._token_expires_at or
            datetime.now() >= (self._token_expires_at - timedelta(minutes=5))):

            print("🔄 Token expired or missing, generating new token...")
            return self.generate_jwt_token()

        print("✅ Using existing valid token")
        return self._current_token

    async def test_api_connection(self) -> bool:
        try:
            token = self.get_valid_token()

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.zoom.us/v2/users/me',
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    user_data = response.json()
                    print(f"✅ API connection successful!")
                    print(f"   📧 User: {user_data.get('email', 'N/A')}")
                    print(f"   🏢 Account: {user_data.get('account_id', 'N/A')}")
                    print(f"   👤 Type: {user_data.get('type', 'N/A')}")
                    return True
                else:
                    print(f"❌ API test failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ API connection error: {e}")
            return False

    async def test_meeting_access(self, meeting_id: str = None) -> bool:
        try:
            token = self.get_valid_token()

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://api.zoom.us/v2/users/me/meetings',
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code == 200:
                    meetings_data = response.json()
                    meeting_count = len(meetings_data.get('meetings', []))
                    print(f"✅ Meeting access successful!")
                    print(f"   📊 Found {meeting_count} meetings")

                    if meeting_id:
                        response = await client.get(
                            f'https://api.zoom.us/v2/meetings/{meeting_id}',
                            headers=headers,
                            timeout=30.0
                        )

                        if response.status_code == 200:
                            meeting_data = response.json()
                            print(f"✅ Specific meeting access successful!")
                            print(f"   📋 Meeting: {meeting_data.get('topic', 'N/A')}")
                            print(f"   🕐 Start: {meeting_data.get('start_time', 'N/A')}")
                        else:
                            print(f"⚠️ Specific meeting not accessible: {response.status_code}")

                    return True
                else:
                    print(f"❌ Meeting access failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ Meeting access error: {e}")
            return False


async def run_comprehensive_auth_test():

    print("🔐 ZOOM AUTHENTICATION FIX")
    print("=" * 60)
    print(f"📅 Test Time: {datetime.now()}")
    print()

    try:
        auth_fix = ZoomJWTAuthFix()

        print("📋 CREDENTIALS CHECK:")
        print(f"   🔑 API Key: {auth_fix.api_key[:8]}..." if auth_fix.api_key else "❌ Missing")
        print(f"   🔐 API Secret: {'✅ Found' if auth_fix.api_secret else '❌ Missing'}")
        print()

        print("🧪 TEST 1: API Connection")
        print("-" * 40)
        api_success = await auth_fix.test_api_connection()
        print()

        print("🧪 TEST 2: Meeting Access")
        print("-" * 40)
        meeting_success = await auth_fix.test_meeting_access()
        print()

        print("🧪 TEST 3: Token Refresh")
        print("-" * 40)
        print("🔄 Generating new token to test refresh...")
        new_token = auth_fix.generate_jwt_token(expires_in_seconds=7200)
        print(f"✅ New token generated: {new_token[:20]}...")
        print()

        print("📊 OVERALL RESULTS")
        print("-" * 40)
        print(f"   API Connection: {'✅ PASS' if api_success else '❌ FAIL'}")
        print(f"   Meeting Access: {'✅ PASS' if meeting_success else '❌ FAIL'}")
        print(f"   Token Refresh: ✅ PASS")

        if api_success and meeting_success:
            print()
            print("🎉 SUCCESS! Your Zoom authentication is now working.")
            print()
            print("🚀 NEXT STEPS:")
            print("   1. Run: python demo_live_test.py")
            print("   2. Test with real meeting: python live_test.py <meeting_id> observer")
            print()
            return True
        else:
            print()
            print("❌ Some tests failed. See recommendations below.")
            return False

    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False


def provide_solutions():

    print("🔧 AUTHENTICATION SOLUTIONS")
    print("=" * 60)
    print()

    print("📝 SOLUTION 1: Refresh Your App (Quick Fix)")
    print("-" * 50)
    print("1. Go to: https://marketplace.zoom.us/user/build")
    print("2. Find your existing app")
    print("3. Go to 'App Credentials' section")
    print("4. Click 'Regenerate' for API Key and Secret")
    print("5. Update your .env file with new credentials")
    print()

    print("📝 SOLUTION 2: Check App Status")
    print("-" * 50)
    print("1. Ensure your app is 'Published' or 'In Development'")
    print("2. Check that all required scopes are enabled:")
    print("   ✅ meeting:read")
    print("   ✅ meeting:write")
    print("   ✅ user:read")
    print("3. Verify app type is 'JWT' (for current credentials)")
    print()

    print("📝 SOLUTION 3: Create New Server-to-Server OAuth App")
    print("-" * 50)
    print("1. Go to: https://marketplace.zoom.us/develop/create")
    print("2. Create 'Server-to-Server OAuth' app")
    print("3. Add scopes: meeting:read:admin, meeting:write:admin, user:read:admin")
    print("4. Get Account ID, Client ID, Client Secret")
    print("5. Update .env with new OAuth credentials")
    print()

    print("📝 SOLUTION 4: Temporary Workaround")
    print("-" * 50)
    print("If you need to test immediately:")
    print("1. Use the demo: python demo_live_test.py")
    print("2. Test audio only: python -m src.audio.recognition")
    print("3. Test AI analysis: python -m src.ai.analyzer")
    print()


if __name__ == "__main__":
    print("🔐 Zoom Authentication Fix")
    print("This script diagnoses and fixes Zoom API authentication issues.")
    print()

    try:
        success = asyncio.run(run_comprehensive_auth_test())

        if not success:
            print()
            provide_solutions()

    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        print()
        provide_solutions()
