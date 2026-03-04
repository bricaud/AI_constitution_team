import os
import yaml
from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import datetime

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
        if agent_name == "ai_activist":
            # Reference document: European Declaration of Digital Rights and Principles
            # https://digital-strategy.ec.europa.eu/en/library/european-declaration-digital-rights-and-principles
            knowledge_sources = [PDFKnowledgeSource(file_paths=["European_Declaration_on_Digital_Rights_and_Principles.pdf"])]
        if agent_name == "ai_digital_advocate":
            # Reference document: the Global Digital Compact (Rev. 1)
            # https://www.un.org/digital-emerging-technologies/sites/www.un.org.techenvoy/files/general/GDC_Rev_3_silence_procedure.pdf
            knowledge_sources = [PDFKnowledgeSource(file_paths=["GDC_Rev_3_silence_procedure.pdf"])]
        if agent_name == "ai_scholar_and_constitutional_translator":
            # Reference document: Digital Constitutionalism: The Role of Internet Bills of Rights
            # https://library.oapen.org/bitstream/handle/20.500.12657/75991/9781000685190.pdf?sequence=1&isAllowed=y
            knowledge_sources = [PDFKnowledgeSource(file_paths=["digitalConstitutionalism.pdf"])]
        if agent_name == "ai_digital_rights_constitutionalist":
            # Reference document: Rights in the Digital Age: A Human Rights Approach to the Governance of AI
            # https://www.idea.int/publications/catalogue/rights-digital-age
            knowledge_sources = [PDFKnowledgeSource(file_paths=["rights-in-the-digital-age.pdf"])]


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
os.makedirs("constitutions", exist_ok=True)
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
        task_details["output_file"] = os.path.join("constitutions", f"{base_name}_{timestamp}{ext}")

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

print("\n\n########################")
print("## FINAL SYNTHESIS OUTPUT ##")
print("########################\n")
print(result.raw)

filename = os.path.join("constitutions", f"draft_constitution_{timestamp}.md")
with open(filename, "w", encoding="utf-8") as f:
    f.write(result.raw)
print(f"\nSaved draft constitution to {filename}")
