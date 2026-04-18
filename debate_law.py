import os
import sys
import json
import warnings
import yaml
import re

warnings.filterwarnings("ignore", category=DeprecationWarning, module="crewai")
from crewai import Agent, Task, Crew, Process, LLM
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from dotenv import load_dotenv
import datetime
from memory_manager import DebateMemory

# --- SETTINGS ---
INCLUDE_SOVEREIGN = True  # Set to False to exclude the authoritarian foil
# ----------------

load_dotenv()
API_key = os.getenv("GOOGLE_API_KEY")

# --- Model Configuration ---
lite_llm = LLM(model="gemini/gemini-2.5-flash-lite", temperature=0.7, api_key=API_key)
pro_llm = LLM(model="gemini/gemini-2.5-pro", temperature=0.3, api_key=API_key)


def list_law_texts(folder="law_texts"):
    return sorted(f for f in os.listdir(folder) if f.endswith(".md"))


def select_law_text(folder="law_texts"):
    files = list_law_texts(folder)
    if not files:
        print(f"No .md files found in '{folder}/'. Add law texts there and re-run.")
        sys.exit(1)

    print("\nAvailable law texts:")
    for i, name in enumerate(files, start=1):
        print(f"  {i}. {name}")

    while True:
        raw = input("\nEnter the number of the law text to debate: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(files):
            chosen = files[int(raw) - 1]
            print(f"\nSelected: {chosen}\n")
            return os.path.join(folder, chosen), chosen
        print(f"Please enter a number between 1 and {len(files)}.")


# --- Select and load law text ---
law_path, law_filename = select_law_text()
with open(law_path, "r", encoding="utf-8") as f:
    law_text = f.read()
law_title = os.path.splitext(law_filename)[0]

# --- Load task templates from YAML ---
def load_template(name):
    path = os.path.join("tasks", f"{name}.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)

templates = {
    name: load_template(name)
    for name in [
        "law_task_debater_opening",
        "law_task_debater_rebuttal1",
        "law_task_debater_rebuttal2",
        "law_task_debater_vote",
        "law_task_opening_summary",
        "law_task_rebuttal1_summary",
        "law_task_rebuttal2_summary",
        "law_task_full_summary",
        "law_task_synthesis",
        "law_task_vote_report",
    ]
}

# --- Load agents ---
agents = {}
for filename in sorted(os.listdir("agents")):
    if not filename.endswith(".yaml"):
        continue
    agent_name = filename.split(".")[0]
    if agent_name == "sovereign_architect" and not INCLUDE_SOVEREIGN:
        continue

    with open(os.path.join("agents", filename), "r") as f:
        agent_details = yaml.safe_load(f)

    if "declaration" in agent_details:
        declaration = agent_details.pop("declaration")
        current_backstory = agent_details.get("backstory", "")
        agent_details["backstory"] = (
            f"{current_backstory}\n\n --- Additional Knowledge ---\n{declaration}"
        )

    knowledge_sources = []
    if "knowledge" in agent_details:
        knowledge_files = agent_details.pop("knowledge")
        if isinstance(knowledge_files, list):
            knowledge_sources = [PDFKnowledgeSource(file_paths=[f]) for f in knowledge_files]
        elif isinstance(knowledge_files, str):
            knowledge_sources = [PDFKnowledgeSource(file_paths=[knowledge_files])]

    if agent_name == "secretary":
        agents[agent_name] = Agent(**agent_details, llm=pro_llm, max_iter=50)
    else:
        # All debaters use lite_llm; no orchestrator needed
        agents[agent_name] = Agent(
            **agent_details,
            llm=lite_llm,
            knowledge_sources=knowledge_sources if knowledge_sources else None,
        )

debaters = {name: agent for name, agent in agents.items() if name != "secretary"}

# --- Output directory ---
base_output_dir = "law_debates"
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
safe_title = re.sub(r"[^\w\-]", "_", law_title)[:40]
output_dir = os.path.join(base_output_dir, f"{timestamp}_{safe_title}")
os.makedirs(output_dir, exist_ok=True)

# Save a copy of the source law for reference
with open(os.path.join(output_dir, "source_law.md"), "w", encoding="utf-8") as f:
    f.write(law_text)

# --- Shared mem0 memory ---
debate_memory = DebateMemory(run_id=timestamp)

# Recalled memories to inject into task descriptions
recalled_memory = debate_memory.recall(topic=law_title, top_k=5, part=0)
memory_note = f"\n\n{recalled_memory}" if recalled_memory else ""

def out(filename):
    """Resolve output file path inside the run's output directory."""
    return os.path.join(output_dir, filename)

def make_task(tmpl_name, description_override=None, agent=None, context=None, output_filename=None):
    tmpl = templates[tmpl_name]
    desc = description_override if description_override is not None else tmpl["description"]
    filename = output_filename or tmpl.get("output_file")
    return Task(
        description=desc,
        expected_output=tmpl["expected_output"],
        output_file=out(filename) if filename else None,
        agent=agent,
        context=context or [],
    )

# ── Round 1: Opening statements (one task per debater) ─────────────────────────
opening_tasks = []
for agent_name, agent in debaters.items():
    desc = templates["law_task_debater_opening"]["description"].format(
        law_title=law_title,
        law_text=law_text,
    ) + memory_note
    t = make_task(
        "law_task_debater_opening",
        description_override=desc,
        agent=agent,
        output_filename=f"opening_{agent_name}.md",
    )
    opening_tasks.append(t)

# Secretary: summarise all opening statements
opening_summary = make_task(
    "law_task_opening_summary",
    agent=agents["secretary"],
    context=opening_tasks,
)

# ── Round 2: First rebuttals (one task per debater) ────────────────────────────
rebuttal1_tasks = []
for agent_name, agent in debaters.items():
    desc = templates["law_task_debater_rebuttal1"]["description"] + memory_note
    t = make_task(
        "law_task_debater_rebuttal1",
        description_override=desc,
        agent=agent,
        context=[opening_summary],
        output_filename=f"rebuttal1_{agent_name}.md",
    )
    rebuttal1_tasks.append(t)

# Secretary: summarise first rebuttals
rebuttal1_summary = make_task(
    "law_task_rebuttal1_summary",
    agent=agents["secretary"],
    context=rebuttal1_tasks,
)

# ── Round 3: Second (closing) rebuttals (one task per debater) ─────────────────
rebuttal2_tasks = []
for agent_name, agent in debaters.items():
    desc = templates["law_task_debater_rebuttal2"]["description"] + memory_note
    t = make_task(
        "law_task_debater_rebuttal2",
        description_override=desc,
        agent=agent,
        context=[opening_summary, rebuttal1_summary],
        output_filename=f"rebuttal2_{agent_name}.md",
    )
    rebuttal2_tasks.append(t)

# Secretary: summarise closing arguments
rebuttal2_summary = make_task(
    "law_task_rebuttal2_summary",
    agent=agents["secretary"],
    context=rebuttal2_tasks,
)

# ── Full debate summary (secretary) ───────────────────────────────────────────
full_summary = make_task(
    "law_task_full_summary",
    agent=agents["secretary"],
    context=[opening_summary, rebuttal1_summary, rebuttal2_summary],
)

# ── Law synthesis: draft revised articles (secretary) ─────────────────────────
synthesis_desc = templates["law_task_synthesis"]["description"].format(
    law_title=law_title
)
synthesis = make_task(
    "law_task_synthesis",
    description_override=synthesis_desc,
    agent=agents["secretary"],
    context=[opening_summary, rebuttal1_summary, rebuttal2_summary, full_summary],
)

# ── Voting: each debater votes on the revised articles ────────────────────────
vote_tasks = []
for agent_name, agent in debaters.items():
    desc = templates["law_task_debater_vote"]["description"].format(
        law_title=law_title
    )
    t = make_task(
        "law_task_debater_vote",
        description_override=desc,
        agent=agent,
        context=[synthesis],
        output_filename=f"vote_{agent_name}.md",
    )
    vote_tasks.append(t)

# Secretary: compile the voting report
vote_report = make_task(
    "law_task_vote_report",
    agent=agents["secretary"],
    context=vote_tasks,
)

# ── Assemble ordered task list ────────────────────────────────────────────────
all_tasks = (
    opening_tasks
    + [opening_summary]
    + rebuttal1_tasks
    + [rebuttal1_summary]
    + rebuttal2_tasks
    + [rebuttal2_summary, full_summary, synthesis]
    + vote_tasks
    + [vote_report]
)

# ── Run ───────────────────────────────────────────────────────────────────────
law_debate_crew = Crew(
    agents=list(agents.values()),
    tasks=all_tasks,
    process=Process.sequential,
    memory=False,
    verbose=True,
    embedder={
        "provider": "google-generativeai",
        "config": {
            "model": "models/embedding-001",
            "api_key": API_key,
            "task_type": "retrieval_document",
        },
    },
)

start_time = datetime.datetime.now()
result = law_debate_crew.kickoff()
end_time = datetime.datetime.now()
print(f"[Output] Results saved to: {output_dir}")


# --- Save metadata file ---
duration = end_time - start_time
metadata = {
    "run_id": timestamp,
    "date": start_time.strftime("%Y-%m-%d"),
    "start_time": start_time.isoformat(timespec="seconds"),
    "end_time": end_time.isoformat(timespec="seconds"),
    "duration_seconds": int(duration.total_seconds()),
    "law_file": law_filename,
    "law_title": law_title,
    "output_dir": output_dir,
    "settings": {
        "include_sovereign": INCLUDE_SOVEREIGN,
    },
    "agents": {
        "debaters": list(debaters.keys()),
        "secretary": "secretary",
    },
    "tasks_count": {
        "opening": len(opening_tasks),
        "rebuttal1": len(rebuttal1_tasks),
        "rebuttal2": len(rebuttal2_tasks),
        "vote": len(vote_tasks),
        "total": len(all_tasks),
    },
    "token_usage": {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "successful_requests": usage.successful_requests,
    },
}

metadata_path = os.path.join(output_dir, "metadata.json")
with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)
print(f"[Metadata] Saved to: {metadata_path}")


# ── Persist outputs to shared memory ─────────────────────────────────────────
named_tasks = (
    [(f"opening_{list(debaters.keys())[i]}", t) for i, t in enumerate(opening_tasks)]
    + [("opening_summary", opening_summary)]
    + [(f"rebuttal1_{list(debaters.keys())[i]}", t) for i, t in enumerate(rebuttal1_tasks)]
    + [("rebuttal1_summary", rebuttal1_summary)]
    + [(f"rebuttal2_{list(debaters.keys())[i]}", t) for i, t in enumerate(rebuttal2_tasks)]
    + [("rebuttal2_summary", rebuttal2_summary), ("full_summary", full_summary), ("synthesis", synthesis)]
    + [(f"vote_{list(debaters.keys())[i]}", t) for i, t in enumerate(vote_tasks)]
    + [("vote_report", vote_report)]
)

try:    
    for task_name, task_obj in named_tasks:
        if task_obj.output and task_obj.output.raw:
            debate_memory.save(content=task_obj.output.raw, task_name=task_name, part=0)

    print(f"\n[DebateMemory] All outputs from run '{timestamp}' saved to shared memory.")
except Exception as e:
    print(f"\n[Error] An error occurred during the record of the memory: {e}")


debate_memory.close()

# --- Token usage report ---
usage = result.token_usage
print("\n── Token Usage ──────────────────────────────")
print(f"  Prompt tokens:     {usage.prompt_tokens:>10,}")
print(f"  Completion tokens: {usage.completion_tokens:>10,}")
print(f"  Total tokens:      {usage.total_tokens:>10,}")
print(f"  Successful calls:  {usage.successful_requests:>10,}")
print("─────────────────────────────────────────────")

