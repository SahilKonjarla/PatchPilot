import asyncio
import os
from dotenv import load_dotenv
from adapters.github.auth import get_installation_token
from adapters.github.comments import post_pr_comment

load_dotenv()  # ensure .env is loaded

async def main():
    repo_full = os.getenv("TEST_REPO", "sahilkonjarla/test_repo")
    pr_number = int(os.getenv("TEST_PR_NUMBER", "1"))
    installation_id = int(os.getenv("TEST_INSTALLATION_ID", "0"))

    if installation_id == 0:
        print("❌ Missing TEST_INSTALLATION_ID in .env")
        return

    token = await get_installation_token(installation_id)
    print("✅ Got installation token")

    body = "👋 PatchPilot test: posting this comment manually!"
    comment = await post_pr_comment(token, repo_full, pr_number, body)

    print(f"✅ Comment posted: {comment['html_url']}")

if __name__ == "__main__":
    asyncio.run(main())
