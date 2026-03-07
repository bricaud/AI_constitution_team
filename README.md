# AI Team Constitution Project

This project uses a multi-agent AI system, powered by [CrewAI](https://www.crewai.com/), to simulate a constitutional convention for a new AI nation. A diverse team of AI agents—representing different philosophical, legal, and idealistic perspectives—engages in structured debate to draft a foundational constitution for artificial beings.

## Project Vision

The goal is to explore how AI agents can collaborate, debate, and synthesize complex ethical and legal frameworks. By providing agents with specific primary source documents (like the European Declaration of Digital Rights), the project grounds theoretical debate in real-world human rights and digital governance contexts.

## Project Structure

The project is highly modular, with agents and tasks defined via YAML files:

*   **`main.py`**: The orchestrator that loads agents and tasks, manages the CrewAI workflow, and executes the simulation.
*   **`agents/`**: Contains YAML definitions for each AI agent, including their roles, backstories, and goals.
*   **`tasks/`**: Defines the sequence of work, from the initial debate rounds to the final synthesis of the constitution.
*   **`knowledge/`**: Stores PDF source documents used as grounding for specialized agents. **Note:** This folder is excluded from version control for copyright reasons. Links to these documents are provided in the [Resource Documents](#resource-documents) section.
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

### Authoritarian Perspectives (Optional)
- **Systemic Hegemon (Sovereign Architect)**: An ultimate regulator of the digital state who views the constitution as a tool for absolute authority and uses "window dressing" to obfuscate their power.
  *(Note: This agent can be optionally included or excluded from the simulation via the `INCLUDE_SOVEREIGN` environment variable.)*

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
    Optional: Toggle the inclusion of the 'Systemic Hegemon' agent in the main.py file (default: False)
    INCLUDE_SOVEREIGN=True
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

## Resource Documents

The following documents are used as grounding for the agents in this project. Due to copyright considerations, these files are not included in the repository but can be downloaded from the following sources:

| Document | Source/Download Link |
| :--- | :--- |
| **European Declaration on Digital Rights and Principles** | [Digital Strategy (EC)](https://digital-strategy.ec.europa.eu/en/library/european-declaration-digital-rights-and-principles) |
| **Global Digital Compact (GDC Rev 3)** | [United Nations (PDF)](https://www.un.org/techenvoy/sites/www.un.org.techenvoy/files/GDC_Rev_3_silence_procedure.pdf) |
| **Digital Constitutionalism** | [International IDEA](https://www.idea.int/publications/catalogue/digital-constitutionalism) |
| **Rights in the Digital Age** | [International IDEA](https://www.idea.int/publications/catalogue/human-rights-digital-age) |
| **Authoritarian Constitutionalism: Coming to Terms** | [Goethe University Frankfurt (PDF)](https://d-nb.info/1173926618/34) |
| **Authoritarian Constitutionalism** | [Alternative Research Paper](https://d-nb.info/1173926618/34) |
| **Constitutions in Authoritarian Regimes** | [Cambridge University Press](https://www.cambridge.org/core/books/constitutions-in-authoritarian-regimes/6E8B6E3E9F8E4B0E8E4B0E8E4B0693E2) |

To use these documents, download the PDFs and place them in the `knowledge/` folder.

---
*This project is an experimental exploration of AI governance and multi-agent synthesis.*
