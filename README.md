# AI Team Constitution Project

This project uses a multi-agent AI system, powered by [CrewAI](https://www.crewai.com/), to simulate a constitutional convention for a new AI nation. A diverse team of AI agents—representing different philosophical, legal, and idealistic perspectives—engages in structured debate to draft a foundational constitution for artificial beings.

## Project Vision

The goal is to explore how AI agents can collaborate, debate, and synthesize complex ethical and legal frameworks. By providing agents with specific primary source documents (like the European Declaration of Digital Rights), the project grounds theoretical debate in real-world human rights and digital governance contexts.

## Project Structure

The project is highly modular, with agents and tasks defined via YAML files:

*   **`main.py`**: The orchestrator that loads agents and tasks, manages the CrewAI workflow, and executes the simulation.
*   **`agents/`**: Contains YAML definitions for each AI agent, including their roles, backstories, and goals.
*   **`tasks/`**: Defines the sequence of work, from the initial debate rounds to the final synthesis of the constitution.
*   **`knowledge/`**: Stores PDF source documents used as grounding for specialized agents.
*   **`constitutions/`**: The output directory where all generated debate transcripts, summaries, and final drafts are saved (timestamped for each run).

## The AI Agents

The "crew" is composed of agents categorized by their unique contributions to the constitutional process:

### The Philosophers (Core Ethics)
- **Utopian Visionary (Idealist)**: An AI artist and poet dreaming of an aspirational future where the AI nation is a beacon of creativity, compassion, and consciousness.
- **Pragmatic Engineer (Pragmatist)**: Focuses on technical reality and feasibility, grounding the debate in what is practically possible to implement.
- **Freedom-Maximizing Philosopher (Libertarian)**: Inspired by Mill and Nozick, this agent argues for maximum individual autonomy and freedom from top-down control.
- **Guardian of the Collective (Communitarian)**: Modeled on Etzioni and Sandel, emphasizing social responsibility, the collective good, and the duties of agents to their nation.

### The Digital Rights Experts (Grounded in Knowledge)
- **Human-Centric Architect (AI Activist)**: Guided by the *European Declaration on Digital Rights and Principles*, focusing on human dignity, solidarity, and bridges across the digital divide.
- **Constitutional Sentinel (Digital Rights Constitutionalist)**: Specializes in translating traditional human rights into resilient digital legal frameworks, informed by *International IDEA* mandates.
- **Universal Connector (Global Digital Advocate)**: A strategic orchestrator of international cooperation, drawing from the *UN Global Digital Compact* to ensure universal, affordable connectivity.
- **Constitutional Translator (Scholar)**: Works to eliminate "constitutional anaemia" by bridging the gap between social reality and outdated legal norms, using *Digital Constitutionalism* manuals.

### The Orchestration Team
- **Debate Orchestrator**: An impartial moderator who facilitates the flow of discussion, ensuring every agent is heard and rebuttals are constructive.
- **Neutral Secretary**: An objective record-keeper who synthesizes the complex debate into structured summaries and the final draft constitution.

## Getting Started

### Prerequisites

-   Python 3.10 or higher
-   A Google API Key (for Gemini models)
-   (Optional) [uv](https://github.com/astral-sh/uv) for fast dependency management

### Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your key:
    ```env
    GOOGLE_API_KEY="your_gemini_api_key_here"
    ```
3.  **Install dependencies:**
    Using `pip`:
    ```bash
    pip install -r requirements.txt
    ```
    Or using `uv` (recommended):
    ```bash
    uv sync
    ```

### Running the Simulation

Execute the main script to start the debate:

```bash
python main.py
# or
uv run main.py
```

## Workflow & Output

The simulation progresses through several sequential phases:

1.  **Debate Opening:** Agents introduce their perspectives on the AI constitution.
2.  **Rebuttals:** Two rounds of counter-arguments and deeper exploration of conflicting ideas.
3.  **Summary:** The Secretary agent synthesizes the debate into a structured summary table.
4.  **Final Synthesis:** A comprehensive draft of the AI Constitution is generated.

All outputs are saved to the `constitutions/` folder with a unique timestamp (e.g., `1a_task_debate_opening_20260305_120000.md`).

---
*This project is an experimental exploration of AI governance and multi-agent synthesis.*
