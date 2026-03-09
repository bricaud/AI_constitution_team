import os
import yaml
from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import datetime

# Variables
INCLUDE_SOVEREIGN = True # To include the sovereign architect, set to True
PARTS_TO_INCLUDE = [1, 2, 3, 4, 5] # List of part keys from constitution_parts.yaml

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
    temperature=0.4,
    google_api_key=API_key
)

# A more powerful model for the secretary
pro_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    verbose=True,
    temperature=0.4,
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
# Create a timestamped output directory
base_output_dir = "constitutions_challenged" if "sovereign_architect" in agents else "constitutions"
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = os.path.join(base_output_dir, timestamp)
os.makedirs(output_dir, exist_ok=True)

# Define the list of tasks to execute in order
TASKS_ORDER = [
    "1a_task_debate_opening",
    "1ax_task_debate_opening_summary",
    "1b_task_debate_rebuttal1",
    "1bx_task_debate_rebuttal1_summary",
    "1c_task_debate_rebuttal2",
    "1cx_task_debate_rebuttal2_summary",
    "2_task_summary",
    "3_task_synthesis"
]

# Load only the specified tasks
tasks_data = {}
for task_name in TASKS_ORDER:
    file_path = os.path.join("tasks", f"{task_name}.yaml")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            tasks_data[task_name] = yaml.safe_load(f)
    else:
        print(f"Warning: Task file {file_path} not found.")

# Load constitution parts
with open("constitution_parts.yaml", "r") as f:
    common_parts = yaml.safe_load(f)
# Flexible part loading based on PARTS_TO_INCLUDE list
parts_text = "\n\n".join([f"  {common_parts[p]}" for p in PARTS_TO_INCLUDE if p in common_parts])

tasks = {}
for task_name in TASKS_ORDER:
    if task_name not in tasks_data:
        continue
    task_details = tasks_data[task_name]
    
    # Get the agent for the task
    if "agent" in task_details:
        agent_name = task_details.pop("agent")
    else:
        raise ValueError(f"Task {task_name} has no agent or agents defined.")
    # Get the context for the task
    context_tasks = task_details.pop("context", [])
    # Force secretary for summary and synthesis tasks
    if "_summary" in task_name or "task_synthesis" in task_name:
        agent_name = "secretary"

    context = [tasks[t] for t in context_tasks if t in tasks]

    # Handle placeholders in 1a and 3 tasks
    if "1a_task_debate_opening" in task_name or "3_task_synthesis" in task_name:
        task_details["description"] = task_details["description"].format(
            parts=parts_text
        )

    # If it is the debate task, add the list of agents to the description
    if "task_debate" in task_name and "_summary" not in task_name:
        # Only philosophers/activists should debate, not the orchestrator or secretary
        debaters_list = [name for name in agents.keys() if name not in ["orchestrator", "secretary"]]
        task_details["description"] += (
            f"\n\nPreside over the debate between: {', '.join(debaters_list)}."
            " Use delegation tools to call on EACH agent once. "
            " Require a 'Knowledge Retrieved' section at the bottom. "
            " CRITICAL: Instruct all agents to be CONCISE (max 250 words per turn). "
            " Output the full transcript. Start each turn with the speaker's name and a brief summary."
        )
        # If there is a summary of the previous round in context, remind the agents
        if any("_summary" in c_task.description for c_task in context): # Simple check for summary tasks
             task_details["description"] += "\n\nCRITICAL: Refer to the provided summary of arguments from previous rounds to avoid repetition and ensure a deeper level of engagement with the other agents' positions."

    # Modify output_file if it exists to include task name and directory
    if "output_file" in task_details:
        original_output = task_details["output_file"]
        base_name, ext = os.path.splitext(original_output)
        task_details["output_file"] = os.path.join(output_dir, f"{task_name}_{base_name}{ext}")

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
