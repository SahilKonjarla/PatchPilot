import httpx

GITHUB_API = "https://api.github.com"

async def post_pr_comment(token: str, repo_full: str, pr_number: int, body: str):
    """Post a review comment on a PR (general comment, not inline)."""
    url = f"{GITHUB_API}/repos/{repo_full}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, headers=headers, json={"body": body})
        r.raise_for_status()
        return r.json()
