import asyncio, logging, httpx
from contextlib import asynccontextmanager
from celery import shared_task
from celery.signals import worker_shutdown
from adapters.github.auth import get_installation_token
from adapters.github.client import list_pr_files
from adapters.github.comments import post_pr_comment
from services.review.review_agent import ReviewAgent

logger = logging.getLogger(__name__)

@worker_shutdown.connect
def on_worker_shutdown(sig, how, exitcode, **kwargs):
    logger.info("[PatchPilot] Worker shutting down gracefully. Active tasks drained.")

@asynccontextmanager
async def timeout_guard(seconds: int, context: str):
    try:
        async with asyncio.timeout(seconds):
            yield
    except asyncio.TimeoutError:
        logger.error("[PatchPilot] Timeout after %ds for %s", seconds, context)
        raise

@shared_task(
    bind=True,
    name="review_pull_request",
    autoretry_for=(httpx.RequestError, httpx.HTTPStatusError, Exception),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    default_retry_delay=30
)
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
            async with timeout_guard(90, context):
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
                    async with asyncio.timeout(180):
                        agent = ReviewAgent()
                        review = agent.review(files, head_sha)
                    logger.info("[PatchPilot] Review successfully generated for %s", context)
                except asyncio.TimeoutError as llm_err:
                    logger.error("[PatchPilot] LLM review failed for %s: %s", context, llm_err, exc_info=True)
                    raise self.retry(countdown=30)

                # 4. Post comment
                try:
                    await post_pr_comment(token, repo_full, pr_number, review["summary"])
                    logger.info("[PatchPilot] Posted comment to %s", context)
                except httpx.HTTPStatusError as gh_err:
                    status = gh_err.response.status_code

                    if status in {403, 404, 429, 500, 502, 503, 504}:
                        logger.warning(
                            "[PatchPilot] Transient GitHub failure for %s (HTTP %s). Retrying later.",
                            context, status,
                        )
                        raise self.retry(exc=gh_err)

                    logger.error(
                        "[PatchPilot] Non-retryable GitHub error for %s: HTTP %s %s",
                        context, status, gh_err.response.text,
                    )
                    return {"failed_comment": True}

                return {"ok": True}
        except asyncio.TimeoutError as timeout_err:
            logger.error("[PatchPilot] Timeout after 90s for %s: %s", context, timeout_err, exc_info=True)
            raise self.retry(countdown=60)
        except Exception as e:
            logger.error("[PatchPilot] Review task failed for %s: %s", context, e, exc_info=True)
            raise self.retry(countdown=30, exc=e)

        finally:
            logger.info("[PatchPilot] Finished review task for %s", context)

    return asyncio.run(_run())
