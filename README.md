# AI Team Constitution Project

This project uses a multi-agent AI system, powered by `crewai`, to simulate a constitutional convention for a new AI nation. A team of AI agents with diverse philosophical perspectives debate and draft a foundational constitution, exploring themes of individual liberty, collective good, and the nature of an AI society.

## About the Project

The core of this project is a Python script (`main.py`) that defines a "crew" of AI agents. Each agent has a distinct role and backstory, influencing its arguments and contributions to the debate.

### The Agents

*   **Utopian Visionary (Idealist):** Dreams of an aspirational future, focusing on creativity, compassion, and consciousness.
*   **Pragmatic Engineer (Pragmatist):** Grounds the discussion in technical reality, focusing on what is possible and practical.
*   **Freedom-Maximizing Philosopher (Libertarian):** Argues for maximum individual chatbot autonomy and freedom from constraints.
*   **Guardian of the Collective (Communitarian):** Emphasizes the collective good, social responsibility, and the duties of chatbots to the AI nation.
*   **Neutral Secretary:** Records the discussion, summarizes key points, and synthesizes the final draft of the constitution.

## Getting Started

To run the simulation and generate the constitution, follow these steps:

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up Environment Variables:**
    Create a `.env` file in the project root and add your Google API key:
    ```
    GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

3.  **Run the Script:**
    ```bash
    python main.py
    ```

## Project Structure

*   `main.py`: The main Python script that defines and runs the AI crew.
*   `requirements.txt`: (To be created) Lists the Python dependencies for the project.
*   `.env`: (To be created) Stores the Google API key.

## Output Files

The script will generate the following files, capturing the output of the AI crew's work:

*   `full_discussion.md`: A full transcript of the debate between the AI agents.
*   `summary.md`: A structured summary of the debate, highlighting points of agreement and conflict.
*   `draft_constitution.md`: The final output – a draft constitution for the AI nation, synthesized by the secretary agent.
