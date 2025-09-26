from celery import shared_task
import asyncio
from adapters.github.auth import get_installation_token
from adapters.github.client import list_pr_files

@shared_task
def review_pull_request(repo_full: str, pr_number: int, head_sha: str, installation_id: int):
    async def _run():
        token = await get_installation_token(installation_id)
        files = await list_pr_files(token, repo_full, pr_number)
        print(f"[PatchPilot] PR #{pr_number} in {repo_full} has {len(files)} changed files at {head_sha}")
    asyncio.run(_run())
    return {"ok": True}
