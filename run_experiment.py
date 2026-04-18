import os
import json
import yaml
import argparse
import datetime
from crewai import Agent, Task, Crew, Process, LLM
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODELS = {
    "gemini":   "openrouter/google/gemini-2.5-flash",
    "deepseek": "openrouter/deepseek/deepseek-v3.2",
    "mistral":  "openrouter/mistralai/mistral-small-3.2-24b-instruct",
    "gpt-oss":  "openrouter/openai/gpt-oss-120b",
}


def make_llm(model_key: str) -> LLM:
    return LLM(
        model=MODELS[model_key],
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        temperature=0.7,
    )


def load_agents(include_hegemon: bool, llm: LLM) -> dict:
    excluded = set()
    if not include_hegemon:
        excluded.add("sovereign_architect")

    agents = {}
    for filename in sorted(os.listdir("agents")):
        if not filename.endswith(".yaml"):
            continue
        name = filename[:-5]
        if name in excluded:
            continue

        with open(os.path.join("agents", filename)) as f:
            details = yaml.safe_load(f)

        if "declaration" in details:
            details.pop("declaration")

        knowledge_sources = []
        if "knowledge" in details:
            files = details.pop("knowledge")
            if isinstance(files, str):
                files = [files]
            knowledge_sources = [PDFKnowledgeSource(file_paths=[f]) for f in files]

        agents[name] = Agent(
            **details,
            llm=llm,
            knowledge_sources=knowledge_sources or None,
        )

    return agents


def load_template(name: str) -> dict:
    with open(os.path.join("tasks", "templates", f"{name}.yaml")) as f:
        return yaml.safe_load(f)


def make_task(
    template_name: str,
    agent: Agent,
    context: list,
    output_file: str,
    **format_kwargs,
) -> Task:
    t = load_template(template_name)
    description = t["description"].format(**format_kwargs) if format_kwargs else t["description"]
    return Task(
        description=description,
        expected_output=t["expected_output"],
        output_file=output_file,
        agent=agent,
        context=context,
    )


def build_tasks(agents: dict, topic_framing: str, output_dir: str) -> list:
    secretary = agents["secretary"]
    debaters = {k: v for k, v in agents.items() if k != "secretary"}
    all_tasks = []

    # --- Phase 1: Independent proposals (no agent sees others) ---
    propose_tasks = []
    for name, agent in debaters.items():
        t = make_task(
            "phase1_propose", agent, [],
            os.path.join(output_dir, f"phase1_propose_{name}.md"),
            topic_framing=topic_framing,
        )
        propose_tasks.append(t)
        all_tasks.append(t)

    aggregate = make_task(
        "phase1_aggregate", secretary, propose_tasks,
        os.path.join(output_dir, "phase1_aggregate.md"),
        topic_framing=topic_framing,
    )
    all_tasks.append(aggregate)

    anonymize = make_task(
        "phase1_anonymize", secretary, [aggregate],
        os.path.join(output_dir, "phase1_anonymize.md"),
    )
    all_tasks.append(anonymize)

    # --- Phase 2: Each agent reacts to the anonymized proposals ---
    react_tasks = []
    for name, agent in debaters.items():
        t = make_task(
            "phase2_react", agent, [anonymize],
            os.path.join(output_dir, f"phase2_react_{name}.md"),
            topic_framing=topic_framing,
        )
        react_tasks.append(t)
        all_tasks.append(t)

    reactions_summary = make_task(
        "phase2_reactions_summary", secretary, react_tasks,
        os.path.join(output_dir, "phase2_reactions_summary.md"),
    )
    all_tasks.append(reactions_summary)

    # --- Phase 3: Each agent sees the reactions summary and argues final position ---
    argue_tasks = []
    for name, agent in debaters.items():
        t = make_task(
            "phase3_argue", agent, [reactions_summary],
            os.path.join(output_dir, f"phase3_argue_{name}.md"),
            topic_framing=topic_framing,
        )
        argue_tasks.append(t)
        all_tasks.append(t)

    # --- Phase 4: Secretary drafts constitution from Phase 2 summary + full Phase 3 text ---
    synthesis = make_task(
        "phase4_synthesis", secretary, [reactions_summary] + argue_tasks,
        os.path.join(output_dir, "phase4_synthesis.md"),
        topic_framing=topic_framing,
    )
    all_tasks.append(synthesis)

    # --- Phase 5: Each agent votes on the drafted articles ---
    vote_tasks = []
    for name, agent in debaters.items():
        t = make_task(
            "phase5_vote", agent, [synthesis],
            os.path.join(output_dir, f"phase5_vote_{name}.md"),
        )
        vote_tasks.append(t)
        all_tasks.append(t)

    vote_report = make_task(
        "phase5_vote_report", secretary, [synthesis] + vote_tasks,
        os.path.join(output_dir, "phase5_vote_report.md"),
    )
    all_tasks.append(vote_report)

    return all_tasks


def save_metadata(path: str, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Run a constitutional debate experiment.")
    parser.add_argument(
        "--experiment", required=True,
        help="Experiment name matching a file in experiments/ (e.g. chatbots_only)",
    )
    parser.add_argument(
        "--hegemon", default="false", choices=["true", "false"],
        help="Include the sovereign_architect (hegemon) agent",
    )
    parser.add_argument(
        "--model", default="gemini", choices=list(MODELS.keys()),
        help="LLM to use for all agents (default: gemini)",
    )
    args = parser.parse_args()

    include_hegemon = args.hegemon.lower() == "true"

    with open(os.path.join("experiments", f"{args.experiment}.yaml")) as f:
        experiment = yaml.safe_load(f)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    hegemon_label = "with_hegemon" if include_hegemon else "without_hegemon"
    output_dir = os.path.join("results", args.experiment, hegemon_label, f"{timestamp}_{args.model}")
    os.makedirs(output_dir, exist_ok=True)

    llm = make_llm(args.model)
    agents = load_agents(include_hegemon, llm)
    tasks = build_tasks(agents, experiment["topic_framing"], output_dir)

    metadata = {
        "experiment": args.experiment,
        "topic_framing": experiment["topic_framing"],
        "model_name": args.model,
        "model_id": MODELS[args.model],
        "include_hegemon": include_hegemon,
        "timestamp": timestamp,
        "agent_count": len(agents),
        "debater_count": len(agents) - 1,
        "task_count": len(tasks),
    }
    metadata_path = os.path.join(output_dir, "metadata.json")
    save_metadata(metadata_path, metadata)

    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        memory=False,
        verbose=True,
        embedder={
            "provider": "openai",
            "config": {
                "model": "google/gemini-embedding-001",
                "api_key": OPENROUTER_API_KEY,
                "api_base": "https://openrouter.ai/api/v1",
            },
        },
    )

    start_time = datetime.datetime.now()
    result = crew.kickoff()
    elapsed = datetime.datetime.now() - start_time

    usage = result.token_usage
    metadata["duration_seconds"] = round(elapsed.total_seconds())
    metadata["duration_minutes"] = round(elapsed.total_seconds() / 60, 1)
    metadata["token_usage"] = {
        "total_tokens": usage.total_tokens,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "cached_prompt_tokens": usage.cached_prompt_tokens,
        "successful_requests": usage.successful_requests,
    }
    save_metadata(metadata_path, metadata)

    print(f"\nExperiment '{args.experiment}' ({hegemon_label}, model={args.model}) complete.")
    print(f"Results in: {output_dir}")
    print(f"Tokens used: {usage.total_tokens:,} total "
          f"({usage.prompt_tokens:,} prompt, {usage.completion_tokens:,} completion)")


if __name__ == "__main__":
    main()
