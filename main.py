import os
import yaml
from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import datetime

# Variables
INCLUDE_SOVEREIGN = True # To include the sovereign architect, set to True

load_dotenv()

# 1. Setup your single Gemini API Key
API_key = os.getenv("GOOGLE_API_KEY")

# 2. Configure the Gemini Model (shared by all bots)
lite_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    verbose=True,
    temperature=0.7,
    google_api_key=API_key
)

# A more powerful model for the Orchestrator/Manager
flash_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    verbose=True,
    temperature=0.7,
    google_api_key=API_key
)

# A more powerful model for the secretary
pro_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    verbose=True,
    temperature=0.7,
    google_api_key=API_key
)

# Load agents from YAML files in the 'agents' directory
agents = {}
for filename in os.listdir("agents"):
    if filename.endswith(".yaml"):
        agent_name = filename.split(".")[0]
        with open(os.path.join("agents", filename), "r") as f:
            agent_details = yaml.safe_load(f)

        # Make Sovereign Architect optional via environment variable
        if agent_name == "sovereign_architect" and not INCLUDE_SOVEREIGN:
            continue # Skip this agent

        if "declaration" in agent_details:
            declaration = agent_details.pop("declaration")
            current_backstory = agent_details.get("backstory", "")
            agent_details["backstory"] = f"{current_backstory}\n\n --- Additional Knowledge ---\n{declaration}"

        knowledge_sources = []
        if "knowledge" in agent_details:
            knowledge_files = agent_details.pop("knowledge")
            if isinstance(knowledge_files, list):
                knowledge_sources = [PDFKnowledgeSource(file_paths=[f]) for f in knowledge_files]
            elif isinstance(knowledge_files, str):
                knowledge_sources = [PDFKnowledgeSource(file_paths=[knowledge_files])]


        if agent_name == "secretary":
            agents[agent_name] = Agent(
                **agent_details,
                llm=pro_llm,
                max_iter=50
            )
        elif agent_name == "orchestrator":
            agents[agent_name] = Agent(
                **agent_details,
                llm=flash_llm,
                max_iter=50
            )
        else:
            agents[agent_name] = Agent(
                **agent_details,
                llm=lite_llm,
                knowledge_sources=knowledge_sources if knowledge_sources else None
            )

# Load tasks from YAML files in the 'tasks' directory
output_dir = "constitutions_challenged" if "sovereign_architect" in agents else "constitutions"
os.makedirs(output_dir, exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

tasks_data = {}
for filename in os.listdir("tasks"):
    if filename.endswith(".yaml"):
        task_name = filename.split(".")[0]
        with open(os.path.join("tasks", filename), "r") as f:
            tasks_data[task_name] = yaml.safe_load(f)

tasks = {}
for task_name in sorted(tasks_data.keys()):
    task_details = tasks_data[task_name]
    
    # Get the agent for the task
    if "agent" in task_details:
        agent_name = task_details.pop("agent")
    else:
        raise ValueError(f"Task {task_name} has no agent or agents defined.")

    # Get the context for the task
    context_tasks = task_details.pop("context", [])
    context = [tasks[t] for t in context_tasks]

    # If it is the debate task, add the list of agents to the description
    if "task_debate" in task_name:
        # Only philosophers/activists should debate, not the orchestrator or secretary
        debaters_list = [name for name in agents.keys() if name not in ["orchestrator", "secretary"]]
        task_details["description"] += (
            f" You are presiding over this phase of the debate between: {', '.join(debaters_list)}."
            " You must use your delegation tools to call on EACH of these agents to get their perspective."
            " When delegating, explicitly instruct them to first formulate a list of questions, then actively search and cite their provided knowledge base (if they have one) to answer their questions. Only after that, they should use their own reasoning to provide their arguments."
            " Also explicitly instruct them to append a structured 'Knowledge Retrieved' section at the bottom of their response, detailing the exact quotes and documents they found."
            " Ensure the final output contains the full transcript of what they said, including their 'Knowledge Retrieved' sections."
            " Begin each speaker's turn with their name and a one-sentence summary of their perspective."
        )

    # Modify output_file if it exists to include timestamp and directory
    if "output_file" in task_details:
        original_output = task_details["output_file"]
        base_name, ext = os.path.splitext(original_output)
        task_details["output_file"] = os.path.join(output_dir, f"{base_name}_{timestamp}{ext}")

    tasks[task_name] = Task(
        **task_details,
        agent=agents[agent_name],
        context=context
    )

# 5. Form the Crew and Kickoff
ai_constitution_crew = Crew(
    agents=list(agents.values()),
    tasks=list(tasks.values()),
    process=Process.sequential,
    memory=False,
    verbose=True,
    embedder = {
    "provider": "google-generativeai", # Or "google-generativeai"
    "config": {
        "model": "models/embedding-001", # Ensure you use the 'models/' prefix
        "api_key": API_key,
        "task_type": "retrieval_document" # Optional but recommended for RAG
    }
}
)

result = ai_constitution_crew.kickoff()
