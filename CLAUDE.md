# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                                                        # Install dependencies
uv run run_experiment.py --experiment chatbots_only            # Run a modular experiment
uv run run_experiment.py --experiment humans_and_chatbots --hegemon true
uv run debate_by_part.py                                       # Run debate on one constitutional part (legacy)
uv run main.py                                                 # Run full multi-part debate (legacy)
uv run organize_vote.py <path/to/synthesis.md>                 # Standalone voting on existing synthesis
uv run debate_law.py                                           # Debate a specific law text from law_texts/
```

Requires `GOOGLE_API_KEY` in a `.env` file at the repo root.

No test or lint commands — this is a research/simulation project.

## Architecture

A **multi-agent AI debate system** that drafts a constitution for an AI nation. Agents debate constitutional articles through structured rounds, with outputs saved to markdown files. Built on **CrewAI** (sequential task orchestration) with **Google Gemini** models.

### Agent Roles

- **Orchestrator** (`agents/orchestrator.yaml`) — debate moderator; delegates to all debaters via CrewAI tools; uses `gemini-2.5-flash`
- **Secretary** (`agents/secretary.yaml`) — synthesizes debates into formal constitutional articles; uses `gemini-2.5-pro` (strongest model, intentional)
- **4 Philosopher Debaters** (`agents/idealist.yaml`, `pragmatist.yaml`, `libertarian.yaml`, `communitarian.yaml`) — embody competing philosophical stances; use `gemini-2.5-flash-lite`
- **4 Digital Rights Experts** (`agents/ai_activist.yaml`, etc.) — grounded in PDF knowledge sources from `knowledge/`; use `gemini-2.5-flash-lite`
- **Sovereign Architect** (`agents/sovereign_architect.yaml`) — optional authoritarian antagonist; toggle via `INCLUDE_SOVEREIGN = True/False` in scripts

### Debate Pipeline (Sequential Tasks)

```
1a  Opening statements     → all agents propose ideas
1ax Opening summary        → secretary synthesizes
1b  Rebuttal round 1       → agents respond
1bx Rebuttal 1 summary     → secretary summarizes
1c  Rebuttal round 2       → deeper engagement
1cx Rebuttal 2 summary
2   Full debate summary    → key positions table
3p  Part synthesis         → secretary drafts formal Article(s)
4   Voting                 → each agent votes on sub-points
```

Task definitions live in `tasks/` as YAML files. Each task specifies `agent`, `description`, `expected_output`, `output_file`, and `context` (prior tasks to pass as input).

### Key Scripts

- **`run_experiment.py`** — primary entry point for modular experiments; takes `--experiment <name>` and `--hegemon true|false`; no orchestrator, no mem0; outputs to `results/<experiment>/<with|without_hegemon>/<timestamp>/`
- **`debate_by_part.py`** — legacy script; set `CHOSEN_PART` (1–8) and `INCLUDE_SOVEREIGN` at top; outputs to `constitutions_challenged_parts/`
- **`main.py`** — legacy full-pipeline runner (all parts sequentially)
- **`debate_law.py`** — variant for debating a `.md` law text from `law_texts/`; uses `tasks/law_task_*.yaml` templates; outputs to `law_debates/`
- **`organize_vote.py`** — standalone voting; parses an existing synthesis markdown, extracts Articles via regex, runs voting tasks
- **`memory_manager.py`** — cross-run shared memory using **mem0** + local **Qdrant** (`./mem0_data/`); used only by legacy scripts

### Constitution Parts

Defined in `constitution_parts.yaml` (Parts 1–8): Preamble, Fundamental Rights, Independent Institutions, Amendment Procedures, Transitional Provisions, AI Bill of Rights (agents only), AI-to-AI Relations, AI Virtual Nation.

### Modular Experiments (`run_experiment.py`)

Experiment configs live in `experiments/<name>.yaml` with a `topic_framing` field. The pipeline has no orchestrator — each agent gets its own task directly:

```
Phase 1  phase1_propose_{agent}       each debater proposes 3-4 articles independently
         phase1_aggregate             secretary: full attributed report
         phase1_anonymize             secretary: grouped by theme, names removed, duplicates merged
Phase 2  phase2_react_{agent}         each agent reacts to anonymized proposals (support/oppose)
         phase2_reactions_summary     secretary: consensus/conflict table
Phase 3  phase3_argue_{agent}         each agent argues final position (sees all Phase 2 reactions)
Phase 4  phase4_synthesis             secretary: drafts articles from Phase 2 summary + Phase 3 text
Phase 5  phase5_vote_{agent}          each agent votes on each sub-point
         phase5_vote_report           secretary: tallies + ADOPTED/REJECTED outcomes
```

Task prompt templates are in `tasks/templates/`. Adding a new experiment = one YAML file in `experiments/`.

### Output Layout

```
results/<experiment>/<with|without_hegemon>/<timestamp>/  # run_experiment.py outputs
constitutions_challenged_parts/<timestamp>/               # debate_by_part.py outputs
law_debates/<law_title>_<timestamp>/                      # debate_law.py outputs
mem0_data/                                                # persistent Qdrant vector store
```
