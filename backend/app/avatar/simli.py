import base64
from pathlib import Path
import asyncio
import httpx


class SimliAvatarService:

    API_URL = "https://api.simli.ai/static/audio"

    def __init__(
        self,
        api_key: str,
        face_id: str,
        output_dir: str = "storage/video",
    ):
        self.api_key = api_key
        self.face_id = face_id

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @property
    def configured(self) -> bool:
        return bool(
            self.api_key
            and self.face_id
        )

    async def create_session(self) -> dict:
        """
        Creates a short-lived Simli WebRTC session token and retrieves ICE servers.
        This allows the browser to connect securely without receiving the API key.
        """
        if not self.configured:
            raise RuntimeError(
                "Simli avatar is not configured. "
                "Set SIMLI_API_KEY and SIMLI_FACE_ID."
            )

        token_url = "https://api.simli.ai/compose/token"
        ice_url = "https://api.simli.ai/compose/ice"

        payload = {
            "faceId": self.face_id,
            "handleSilence": True,
            "maxSessionLength": 3600,
            "maxIdleTime": 300
        }

        headers = {
            "Content-Type": "application/json",
            "x-simli-api-key": self.api_key,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Get Session Token
            token_response = await client.post(
                token_url,
                json=payload,
                headers=headers,
            )
            token_response.raise_for_status()
            session_data = token_response.json()
            session_token = session_data.get("session_token")

            # 2. Get ICE Servers
            try:
                ice_response = await client.get(
                    ice_url,
                    headers=headers,
                )
                ice_response.raise_for_status()
                ice_servers = ice_response.json()
            except Exception as e:
                # Fallback to standard Google STUN if ICE retrieval fails
                print(f"Warning: Failed to retrieve ICE servers from Simli: {e}")
                ice_servers = [{"urls": ["stun:stun.l.google.com:19302"]}]

        return {
            "session_token": session_token,
            "ice_servers": ice_servers
        }