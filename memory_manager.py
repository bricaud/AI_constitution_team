"""
memory_manager.py
-----------------
Shared mem0 memory layer for the AI constitution debate agents.

Uses the open-source (self-hosted) mem0 stack with:
  - LLM:      Google Gemini (gemini-2.5-flash)
  - Embedder: Google text-embedding-004
  - Vector store: local Qdrant (in-memory / persistent at ./mem0_data)

All agents share the same `run_id` so they can retrieve context from
previous debate sessions.  After each task output is written, call
`save_debate_output()` to persist the result.

Usage
-----
    from memory_manager import DebateMemory

    mem = DebateMemory()
    # Before a task: inject relevant memories
    context_str = mem.recall(topic="individual rights vs collective good", top_k=5)
    # After a task: persist the output
    mem.save(content=task_output, task_name="1a_debate_opening", part=3)
"""

import os
from typing import Optional
from mem0 import Memory
from dotenv import load_dotenv

load_dotenv()

# Shared identifiers
DEBATE_AGENT_ID = "constitution_debate_collective"   # shared memory space for all agents
COLLECTION_NAME = "constitution_debates"


def _build_config(api_key: str) -> dict:
    """Build mem0 config using Google Gemini for LLM + embedder, local Qdrant for storage."""
    return {
        "llm": {
            "provider": "gemini",
            "config": {
                "model": "gemini-2.5-flash",
                "api_key": api_key,
                "temperature": 0.1,
            },
        },
        "embedder": {
            "provider": "gemini",
            "config": {
                # "model": "gemini-embedding-001",
                "model": "gemini-embedding-001",
                "api_key": api_key,
                "embedding_dims": 1536,
            },
        },
        "vector_store": {
            "provider": "qdrant",
            "config": {
                # Persistent local storage – no Docker needed
                "path": "./mem0_data",
                "collection_name": COLLECTION_NAME,
                "on_disk": True,
            },
        },
        "history_db_path": "./mem0_data/history.db",
    }


class DebateMemory:
    """
    Thin wrapper around mem0's Memory class for the debate project.

    All data is stored under the shared `agent_id=DEBATE_AGENT_ID`,
    so every run can access memories from past debates.
    You can optionally pass a `run_id` (e.g. a timestamp) to tag
    memories per debate session and filter them later.
    """

    def __init__(self, run_id: Optional[str] = None):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY is not set in your environment / .env file.")

        os.makedirs("./mem0_data", exist_ok=True)

        self.run_id = run_id
        self.memory = Memory.from_config(_build_config(api_key))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, content: str, task_name: str, part: Optional[int] = None) -> None:
        """
        Persist a debate output chunk into the shared memory.

        Parameters
        ----------
        content   : the text to store (task output, summary, synthesis…)
        task_name : e.g. "1a_task_debate_opening"
        part      : constitution part number, if applicable
        """
        metadata: dict = {"task": task_name}
        if part is not None:
            metadata["part"] = part
        if self.run_id:
            metadata["run_id"] = self.run_id

        messages = [
            {
                "role": "assistant",
                "content": f"[{task_name}] {content}",
            }
        ]
        self.memory.add(
            messages,
            agent_id=DEBATE_AGENT_ID,
            metadata=metadata,
        )
        print(f"[DebateMemory] Saved memory for task='{task_name}' part={part}")

    def recall(self, topic: str, top_k: int = 5, part: Optional[int] = None) -> str:
        """
        Search the shared memory for content relevant to `topic`.

        Returns a formatted string ready to be injected into an agent's
        task description or backstory.

        Parameters
        ----------
        topic : the question / theme to search for
        top_k : maximum number of memories to return
        part  : if set, filter results to only this constitution part
        """
        filters: dict = {}
        if part is not None:
            filters["part"] = part

        results = self.memory.search(
            query=topic,
            agent_id=DEBATE_AGENT_ID,
            limit=top_k,
            filters=filters if filters else None,
        )

        memories = results.get("results", []) if isinstance(results, dict) else results

        if not memories:
            return ""

        lines = ["--- Relevant Debate Memories ---"]
        for i, m in enumerate(memories, 1):
            mem_text = m.get("memory", "")
            score = m.get("score", 0.0)
            meta = m.get("metadata", {})
            tag = meta.get("task", "unknown")
            lines.append(f"{i}. [{tag}] (relevance: {score:.2f}) {mem_text}")
        lines.append("--- End of Memories ---")

        return "\n".join(lines)

    def get_all(self) -> list:
        """Return all stored memories for the shared agent."""
        return self.memory.get_all(agent_id=DEBATE_AGENT_ID)

    def close(self) -> None:
        """
        Explicitly close the underlying vector store client.
        Helps avoid 'ModuleNotFoundError: import of portalocker halted' during shutdown.
        """
        try:
            if hasattr(self.memory, "vector_store") and hasattr(self.memory.vector_store, "client"):
                self.memory.vector_store.client.close()
                print("[DebateMemory] Closed underlying vector store client.")
        except Exception as e:
            print(f"[DebateMemory] Warning: Could not close vector store client: {e}")
