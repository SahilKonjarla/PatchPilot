import logging
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from services.prompts import REVIEW_AGENT_PROMPT
from typing import List, Dict

logger = logging.getLogger(__name__)

class ReviewAgent:
    """
        PatchPilot's AI review agent.
        Orchestrates prompt generation and invokes the selected LLM backend
        to generate actionable PR review feedback.
    """

    def __init__(self, backend: str = "ollama", model: str = "gemma3:4b", temperature: float = 0.2):
        """
            Initialize the review agent with the chosen backend.

            Args:
                backend (str): "ollama" (local) or "openai".
                model (str): Model name to use for LLM.
                temperature (float): Sampling temperature for generation.

            Raises:
                ValueError: If unsupported backend is specified.
        """

        logger.debug(f"[ReviewAgent] Initializing with backend={backend}, model={model}, temp={temperature}")
        if backend == "ollama":
            self.llm = ChatOllama(model=model, temperature=temperature)
        elif backend == "openai":
            self.llm = ChatOpenAI(model=model, temperature=temperature)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def review(self, files: List[Dict], head_sha: str) -> dict:
        """
            Run AI review on PR diffs.

            Args:
                files (List[Dict]): List of GitHub file objects from PR API.
                head_sha (str): Commit SHA of the PR head.

            Returns:
                dict: {"summary": str, "comments": list}

            Raises:
                ValueError: If input `files` is not in the expected format.
                RuntimeError: If LLM invocation fails.
        """

        if isinstance(files, str):
            raise ValueError(f"Expected list of dicts, got string: {files}")

        if not files:
            logger.warning("[ReviewAgent] Called with empty file list.")
            return {"summary": "No files to review.", "comments": []}

        # Format diffs into a single review prompt
        try:
            file_diffs = "\n\n".join(
                f"File: {f.get('filename', '(unknown)')}\nPatch:\n{f.get('patch', '(no diff provided)')}"
                for f in files
            )
        except Exception as e:
            logger.error(f"[ReviewAgent] Failed to format file diffs: {e}", exc_info=True)
            raise

        prompt = REVIEW_AGENT_PROMPT(head_sha, file_diffs)
        logger.debug(f"[ReviewAgent] Generated review prompt for commit {head_sha[:7]} with {len(files)} files.")

        # Run inference
        try:
            res = self.llm.invoke(prompt)
        except Exception as e:
            logger.error(f"[ReviewAgent] LLM invocation failed: {e}", exc_info=True)
            raise RuntimeError("ReviewAgent failed to invoke LLM.") from e

        if not hasattr(res, "content"):
            logger.error(f"[ReviewAgent] Unexpected LLM response format: {res}")
            raise RuntimeError("Invalid response from LLM (missing .content).")

        summary = res.content.strip()
        logger.info(f"[ReviewAgent] Successfully generated review summary for commit {head_sha[:7]}.")

        return {
            "summary": summary,
            "comments": []  # Placeholder: can extend later with inline comments
        }