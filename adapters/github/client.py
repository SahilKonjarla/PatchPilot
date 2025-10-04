import httpx, logging
from typing import Dict, List

GITHUB_API = "https://api.github.com"
logger = logging.getLogger(__name__)


async def list_pr_files(token: str, repo_full: str, pr_number: int) -> List[Dict]:
    """
    Fetch the list of changed files in a pull request.

    Args:
        token (str): GitHub installation access token.
        repo_full (str): Repository full name, e.g., "owner/repo".
        pr_number (int): Pull request number.

    Returns:
        List[Dict]: A list of file metadata dictionaries from GitHub's API.
            Each entry typically contains keys like:
            - filename
            - status (added/modified/removed)
            - additions / deletions
            - patch (diff snippet)
            - blob_url, raw_url, contents_url

    Raises:
        httpx.HTTPStatusError: If the request to GitHub fails.
        RuntimeError: If the response cannot be parsed as JSON.
        ValueError: If the JSON response is not a list.
    """
    url = f"{GITHUB_API}/repos/{repo_full}/pulls/{pr_number}/files?per_page=100"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    logger.info(f"[GitHub] Fetching PR files: repo={repo_full}, pr=#{pr_number}")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"[GitHub] Failed to fetch PR files for {repo_full}#{pr_number}: "
                f"status={e.response.status_code}, body={e.response.text}"
            )
            raise

        try:
            data = r.json()
        except Exception as e:
            logger.error(
                f"[GitHub] Invalid JSON in response for {repo_full}#{pr_number}: {r.text}"
            )
            raise RuntimeError(f"Failed to parse JSON from {url}") from e

        if not isinstance(data, list):
            logger.error(
                f"[GitHub] Unexpected response type for {repo_full}#{pr_number}: {type(data)}"
            )
            raise ValueError(f"Expected list of dicts, got {type(data)}: {data}")

        logger.info(f"[GitHub] Retrieved {len(data)} file(s) for {repo_full}#{pr_number}")
        return data

