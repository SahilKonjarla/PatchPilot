import httpx, logging

GITHUB_API = "https://api.github.com"
logger = logging.getLogger(__name__)


async def post_pr_comment(token: str, repo_full: str, pr_number: int, body: str) -> dict:
    """
    Post a general (non-inline) review comment on a pull request.

    Args:
        token (str): GitHub installation access token.
        repo_full (str): Repository in "owner/repo" format.
        pr_number (int): Pull request number.
        body (str): Markdown body of the comment.

    Returns:
        dict: Parsed JSON response from GitHub API.

    Raises:
        httpx.HTTPStatusError: If GitHub returns a 4xx/5xx error.
        RuntimeError: If JSON parsing fails.
    """
    url = f"{GITHUB_API}/repos/{repo_full}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    logger.info(f"[GitHub] Posting comment to PR #{pr_number} in {repo_full}...")

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.post(url, headers=headers, json={"body": body})
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"[GitHub] Failed to post comment to {repo_full} PR #{pr_number}: {e.response.status_code} {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"[GitHub] Unexpected error posting PR comment: {e}", exc_info=True)
            raise

        try:
            data = r.json()
        except Exception as e:
            logger.error(f"[GitHub] Failed to parse JSON response for PR #{pr_number}: {r.text}")
            raise RuntimeError("Invalid JSON response from GitHub.") from e

        logger.info(f"[GitHub] Successfully posted comment to PR #{pr_number}.")
        return data
