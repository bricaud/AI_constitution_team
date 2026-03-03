import os
import yaml
from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# 1. Setup your single Gemini API Key
API_key = os.getenv("GOOGLE_API_KEY")

# 2. Configure the Gemini Model (shared by all bots)
gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    verbose=True,
    temperature=0.7,
    google_api_key=API_key
)

# A more powerful model for the Orchestrator/Manager
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

        if "declaration" in agent_details:
            declaration = agent_details.pop("declaration")
            current_backstory = agent_details.get("backstory", "")
            agent_details["backstory"] = f"{current_backstory}\n\n --- Additional Knowledge ---\n{declaration}"

        knowledge_sources = []
        if agent_name == "ai_scholar_and_constitutional_translator":
            knowledge_sources = [PDFKnowledgeSource(file_paths=["digitalConstitutionalism.pdf"])]

        if agent_name == "orchestrator":
            agents[agent_name] = Agent(
                **agent_details,
                llm=pro_llm,
                max_iter=50
            )
        else:
            agents[agent_name] = Agent(
                **agent_details,
                llm=gemini_llm,
                knowledge_sources=knowledge_sources if knowledge_sources else None
            )

# Load tasks from YAML files in the 'tasks' directory
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
    if task_name.endswith("task_debate"):
        # Only philosophers/activists should debate, not the orchestrator or secretary
        debaters_list = [name for name in agents.keys() if name not in ["orchestrator", "secretary"]]
        task_details["description"] += (
            f" You are presiding over a debate between: {', '.join(debaters_list)}."
            " You must use your delegation tools to call on EACH of these agents to get their perspective."
            " Structure the debate: first an opening statement from each, then a back-and-forth rebuttal phase."
            " Ensure the final output contains the full transcript of what they said."
            " Begin the transcript with a one-sentence description of each debater's perspective."
        )

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
    embedder={
        "provider": "google-generativeai",
        "config": {
            "model": "models/embedding-001",
            "api_key": API_key,
        }
    }
)

result = ai_constitution_crew.kickoff()

print("\n\n########################")
print("## FINAL SYNTHESIS OUTPUT ##")
print("########################\n")
print(result.raw)
