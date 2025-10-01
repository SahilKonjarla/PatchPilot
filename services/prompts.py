from langchain_core.messages import HumanMessage, SystemMessage

def REVIEW_AGENT_PROMPT(head_sha, files):
    """
        Build the structured prompt for PatchPilot's review agent.

        Args:
            head_sha (str): The commit SHA of the pull request head.
            files (str): Concatenated file diffs or file list with patches.

        Returns:
            list: A sequence of LangChain SystemMessage + HumanMessage
                  to be passed to an LLM (e.g., Ollama/OpenAI).
    """

    # System role: lock down behavior and enforce Markdown format
    system_msg = SystemMessage(
        content="""
            You are PatchPilot, an expert senior engineer performing code reviews.

            Your responsibilities:
            - Analyze the provided pull request changes.
            - Identify issues, suggest improvements, and summarize the intent.
            - Be concise, actionable, and professional.
            - Do NOT include extra commentary or sections beyond what is specified.

            Your output must strictly follow this Markdown structure:

            ## Summary
            - High-level overview (2–3 sentences max)

            ## Bugs / Potential Errors
            - List any logic issues or edge cases
            - If none, write: "No major bugs found."

            ## Missing Tests
            - Note where tests are lacking
            - If none, write: "Test coverage appears sufficient."

            ## Style / Consistency
            - Note readability, naming, or formatting issues
            - If none, write: "No style issues detected."

            ## Performance / Security
            - Note performance bottlenecks or security risks
            - If none, write: "No performance or security concerns."

            ## Suggestions
            - Actionable recommendations for the developer
            """
    )

    # Human role: provide contextual input (commit + file diffs)
    human_msg = HumanMessage(
        content=f"""
            Here are the changed files at commit {head_sha}:

            {files}

            Remember: Follow the structure exactly as outlined above.
            """
    )

    return [system_msg, human_msg]
