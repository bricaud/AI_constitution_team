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

The "crew" consists of several specialized agents:

-   **The Philosophers:** Idealist, Pragmatist, Libertarian, and Communitarian agents who bring core ethical viewpoints to the table.
-   **The Experts:** Specialized agents like the **AI Activist** and **AI Global Digital Advocate**, who are grounded in specific international declarations and digital rights frameworks.
-   **The Synthesis Team:** An **Orchestrator** who manages the debate flow and a **Secretary** responsible for summarizing and drafting the final document into a structured Markdown table and final constitution.

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
