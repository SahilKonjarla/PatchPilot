from celery import shared_task
import asyncio
from adapters.github.auth import get_installation_token
from adapters.github.client import list_pr_files
from adapters.github.comments import post_pr_comment
from services.review.review_agent import ReviewAgent

@shared_task
def review_pull_request(repo_full: str, pr_number: int, head_sha: str, installation_id: int):
    async def _run():
        token = await get_installation_token(installation_id)
        files = await list_pr_files(token, repo_full, pr_number)

        file_text = "\n".join(f["filename"] for f in files)

        agent = ReviewAgent()
        review = agent.review(file_text, head_sha)
        # Basic demo: comment with file count
        await post_pr_comment(token, repo_full, pr_number, review["summary"])

        print(f"[PatchPilot] Posted comment on PR #{pr_number} in {repo_full}")
    asyncio.run(_run())
    return {"ok": True}
