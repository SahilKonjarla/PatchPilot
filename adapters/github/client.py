import httpx
from typing import Dict, List

GITHUB_API = "https://api.github.com"

async def list_pr_files(token: str, repo_full: str, pr_number: int) -> List[Dict]:
    url = f"{GITHUB_API}/repos/{repo_full}/pulls/{pr_number}/files?per_page=100"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        try:
            data = r.json()
        except Exception as e:
            raise RuntimeError(f"Failed to parse JSON from {url}: {r.text}") from e
        print(data)
        if not isinstance(data, list):
            raise ValueError(f"Expected list of dicts, got {type(data)}: {data}")
        return data
