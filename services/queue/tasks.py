from celery import shared_task
import asyncio
import logging
from adapters.github.auth import get_installation_token
from adapters.github.client import list_pr_files
from adapters.github.comments import post_pr_comment
from services.review.review_agent import ReviewAgent

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="review_pull_request")
def review_pull_request(self, repo_full: str, pr_number: int, head_sha: str, installation_id: int):
    async def _run():
        try:
            logger.info(f"[PatchPilot] Starting review for PR #{pr_number} in {repo_full}")

            # 1. Auth
            token = await get_installation_token(installation_id)
            logger.info("[PatchPilot] Got installation token.")

            # 2. Get files
            files = await list_pr_files(token, repo_full, pr_number)
            if not isinstance(files, list) or not all(isinstance(f, dict) for f in files):
                raise ValueError(f"Expected list of dicts, got {type(files)} with contents: {files}")
            logger.info(f"[PatchPilot] Raw files response type: {type(files)}")
            logger.info(f"[PatchPilot] Raw files response: {files}")
            if not files:
                logger.info(f"[PatchPilot] No files found for PR #{pr_number}, skipping review.")
                return {"skipped": True}

            # 3. Run agent
            agent = ReviewAgent()
            review = agent.review(files, head_sha)
            logger.info("[PatchPilot] Review generated.")

            # 4. Post comment
            await post_pr_comment(token, repo_full, pr_number, review["summary"])
            logger.info(f"[PatchPilot] Posted comment on PR #{pr_number} in {repo_full}")

            return {"ok": True}

        except Exception as e:
            logger.error(f"Review failed for PR #{pr_number} in {repo_full}: {e}", exc_info=True)
            raise

    return asyncio.run(_run())
