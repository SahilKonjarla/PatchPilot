import asyncio, logging
from celery import shared_task
from adapters.github.auth import get_installation_token
from adapters.github.client import list_pr_files
from adapters.github.comments import post_pr_comment
from services.review.review_agent import ReviewAgent

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="review_pull_request", max_retries=3, default_retry_delay=30)
def review_pull_request(self, repo_full: str, pr_number: int, head_sha: str, installation_id: int):
    """
        Celery task: run an AI-powered review on a GitHub Pull Request.

        Steps:
          1. Authenticate as installation (App token).
          2. Fetch changed PR files.
          3. Run ReviewAgent for analysis.
          4. Post review as a GitHub PR comment.

        Retries:
          - Will retry up to 3 times with exponential backoff
            if GitHub/LLM/network errors occur.
    """

    async def _run():
        context = f"PR #{pr_number} in {repo_full}"
        try:
            logger.info("[PatchPilot] Starting review for %s", context)

            # 1. Auth
            token = await get_installation_token(installation_id)
            if not token:
                raise RuntimeError("Failed to obtain installation token")
            logger.info("[PatchPilot] Installation token acquired for %s", context)

            # 2. Get files
            files = await list_pr_files(token, repo_full, pr_number)
            if not isinstance(files, list) or not all(isinstance(f, dict) for f in files):
                raise ValueError(f"Unexpected response for PR files: {files}")
            logger.info("[PatchPilot] Retrieved %d file(s) for %s", len(files), context)

            if not files:
                logger.warning("[PatchPilot] No files changed in %s, skipping review", context)
                return {"skipped": True}

            # 3. Run agent
            try:
                agent = ReviewAgent()
                review = agent.review(files, head_sha)
                logger.info("[PatchPilot] Review successfully generated for %s", context)
            except Exception as llm_err:
                logger.error("[PatchPilot] LLM review failed for %s: %s", context, llm_err, exc_info=True)
                raise

            # 4. Post comment
            try:
                await post_pr_comment(token, repo_full, pr_number, review["summary"])
                logger.info("[PatchPilot] Posted comment to %s", context)
            except Exception as gh_err:
                logger.error("[PatchPilot] Failed to post comment to %s: %s", context, gh_err, exc_info=True)
                raise

            return {"ok": True}

        except Exception as e:
            logger.error("[PatchPilot] Review task failed for %s: %s", context, e, exc_info=True)
            raise self.retry(exc=e)

    return asyncio.run(_run())
