import os, time, httpx, jwt, logging
from dotenv import load_dotenv

# Load env vars from .env (useful for local dev)
load_dotenv()

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
_PRIVATE_KEY_PEM = os.getenv("GITHUB_PRIVATE_KEY_PEM")

if not _PRIVATE_KEY_PEM:
    raise RuntimeError("Missing GITHUB_PRIVATE_KEY_PEM in environment")

if not GITHUB_APP_ID:
    raise RuntimeError("Missing GITHUB_APP_ID in environment")


def make_app_jwt() -> str:
    """
    Generate a short-lived JWT for GitHub App authentication.

    Returns:
        str: Encoded JWT signed with the GitHub App's private key.

    Raises:
        Exception: If JWT encoding fails.
    """
    now = int(time.time())
    payload = {
        "iat": now - 60,        # Issued 1 minute ago (clock skew buffer)
        "exp": now + (9 * 60),  # Valid for 9 minutes
        "iss": GITHUB_APP_ID,   # GitHub App ID
    }

    logger.debug("[GitHubAuth] Generating JWT for GitHub App authentication.")
    try:
        token = jwt.encode(payload, _PRIVATE_KEY_PEM, algorithm="RS256")
        return token
    except Exception as e:
        logger.error(f"[GitHubAuth] Failed to generate JWT: {e}", exc_info=True)
        raise


async def get_installation_token(installation_id: int) -> str:
    """
    Exchange App JWT for an installation access token.

    Args:
        installation_id (int): GitHub installation ID.

    Returns:
        str: Installation access token scoped to that repo/installation.

    Raises:
        httpx.HTTPStatusError: If GitHub API returns a failure.
        KeyError: If 'token' key missing from GitHub response.
    """
    jwt_token = make_app_jwt()
    url = f"{GITHUB_API}/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }

    logger.info(f"[GitHubAuth] Requesting installation token for installation_id={installation_id}")

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.post(url, headers=headers)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"[GitHubAuth] Failed to fetch installation token: "
                f"status={e.response.status_code}, body={e.response.text}"
            )
            raise

        try:
            data = r.json()
            token = data["token"]
        except Exception as e:
            logger.error(f"[GitHubAuth] Invalid JSON in installation token response: {r.text}")
            raise RuntimeError("Failed to parse installation token from GitHub response.") from e

        logger.info(f"[GitHubAuth] Successfully obtained installation token for installation_id={installation_id}")
        return token
