import asyncio
import os
from dotenv import load_dotenv
from adapters.github.auth import get_installation_token
from adapters.github.client import list_pr_files
from adapters.github.comments import post_pr_comment
from services.review.review_agent import ReviewAgent

load_dotenv()

async def main():
    repo_full = os.getenv("TEST_REPO", "sahilkonjarla/test_repo")
    pr_number = int(os.getenv("TEST_PR_NUMBER", "1"))
    installation_id = int(os.getenv("TEST_INSTALLATION_ID", "0"))

    if installation_id == 0:
        print("❌ Missing TEST_INSTALLATION_ID in .env")
        return

    # 1. Authenticate with GitHub
    token = await get_installation_token(installation_id)
    print("✅ Got installation token")

    # 2. Fetch changed files from the PR
    files = await list_pr_files(token, repo_full, pr_number)
    if not files:
        print("⚠️ No changed files found")
        return

    # For now: join filenames and patch blobs into text
    file_text = "\n".join(f"{f['filename']}:\n{f.get('patch','')}" for f in files)

    # 3. Run review agent
    agent = ReviewAgent(backend="ollama")
    review = agent.review(file_text, "test-sha")

    # 4. Post AI review as a comment on the PR
    comment = await post_pr_comment(token, repo_full, pr_number, review["summary"])
    print(f"✅ Review comment posted: {comment['html_url']}")

if __name__ == "__main__":
    asyncio.run(main())
