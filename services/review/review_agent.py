from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from services.prompts import REVIEW_AGENT_PROMPT
from typing import List, Dict, Union

class ReviewAgent:
    def __init__(self, backend: str = "ollama", model: str = "gemma3:4b", temperature: float = 0.2):
        if backend == "ollama":
            self.llm = ChatOllama(model=model, temperature=temperature)
        elif backend == "openai":
            self.llm = ChatOpenAI(model=model, temperature=temperature)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def review(self, files: Union[List[Dict]], head_sha: str) -> dict:
        """
            Run AI review on PR diffs.
            Returns: {"summary": str, "comments": list}
        """
        if isinstance(files, str):
            raise ValueError(f"Expected list of dicts, got string: {files}")

        file_diffs = "\n\n".join(
            f"File: {f['filename']}\nPatch:\n{f.get('patch', '(no diff provided)')}"
            for f in files
        )
        prompt = REVIEW_AGENT_PROMPT(head_sha, file_diffs)
        res = self.llm.invoke(prompt)
        return {
            "summary": res.content.strip(),
            "comments": []
        }