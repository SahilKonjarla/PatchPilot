import asyncio
import os
from adapters.github.client import list_pr_files
from adapters.github.auth import get_installation_token

async def main():
    # Pull env vars
    repo_full = os.getenv("TEST_REPO", "sahilkonjarla/test_repo")
    pr_number = int(os.getenv("TEST_PR_NUMBER", "1"))
    installation_id = int(os.getenv("TEST_INSTALLATION_ID", "0"))

    if installation_id == 0:
        print("❌ Please set TEST_INSTALLATION_ID in your .env (from webhook payload).")
        return

    # Step 1: Exchange App JWT for installation token
    token = await get_installation_token(installation_id)
    print(f"✅ Got installation token (first 10 chars): {token[:10]}...")

    # Step 2: Call GitHub API
    files = await list_pr_files(token, repo_full, pr_number)
    print(f"✅ PR #{pr_number} has {len(files)} changed files:")
    for f in files:
        print(f" - {f['filename']}")

if __name__ == "__main__":
    asyncio.run(main())
