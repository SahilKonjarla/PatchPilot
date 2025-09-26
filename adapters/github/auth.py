import os, time
import httpx
import jwt
from dotenv import load_dotenv

load_dotenv()

GITHUB_API = "https://api.github.com"
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
_PRIVATE_KEY_PEM = os.getenv("GITHUB_PRIVATE_KEY_PEM")

if not _PRIVATE_KEY_PEM:
    raise RuntimeError("❌ Missing GITHUB_PRIVATE_KEY_PEM in environment")

def make_app_jwt() -> str:
    """Generate a short-lived JWT for GitHub App authentication."""
    now = int(time.time())
    payload = {
        "iat": now - 60,           # issued 1 min ago
        "exp": now + (9 * 60),     # valid for 9 min
        "iss": GITHUB_APP_ID,             # GitHub App ID
    }
    return jwt.encode(payload, _PRIVATE_KEY_PEM, algorithm="RS256")

async def get_installation_token(installation_id: int) -> str:
    """Exchange App JWT for an installation access token."""
    jwt_token = make_app_jwt()
    url = f"{GITHUB_API}/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, headers=headers)
        r.raise_for_status()
        return r.json()["token"]
