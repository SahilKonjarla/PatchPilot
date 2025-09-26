from celery import shared_task
import asyncio
from adapters.github.auth import get_installation_token
from adapters.github.client import list_pr_files
from adapters.github.comments import post_pr_comment

@shared_task
def review_pull_request(repo_full: str, pr_number: int, head_sha: str, installation_id: int):
    async def _run():
        token = await get_installation_token(installation_id)
        files = await list_pr_files(token, repo_full, pr_number)

        # Basic demo: comment with file count
        comment_body = f"👋 PatchPilot here! I see {len(files)} files changed in this PR (head SHA `{head_sha[:7]}`)."
        await post_pr_comment(token, repo_full, pr_number, comment_body)

        print(f"[PatchPilot] Posted comment on PR #{pr_number} in {repo_full}")
    asyncio.run(_run())
    return {"ok": True}
