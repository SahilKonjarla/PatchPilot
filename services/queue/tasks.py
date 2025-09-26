from celery import shared_task

@shared_task
def review_pull_request(repo_full: str, pr_number: int, head_sha: str, installation_id: int):
    print(f"[PatchPilot] Task received for {repo_full} PR #{pr_number} @ {head_sha} (installation={installation_id})")
    return {"repo": repo_full, "pr": pr_number, "head": head_sha, "installation": installation_id}