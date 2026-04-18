# AI Team — Project Summary

> A multi-agent AI system that simulates a **constitutional convention for AI nations**, using CrewAI and Google Gemini to hold structured philosophical debates and draft constitutional articles.

---

## What the Project Does

The system assembles a "crew" of AI agents, each embodying a different political philosophy or domain expertise, and puts them through a structured debate pipeline. The output is a **draft AI Constitution** — a formal, numbered legal document that tries to reconcile the agents' opposing viewpoints.

The constitution is built modularly, **one thematic Part at a time** (e.g. Preamble, Bill of Rights, Amendment Procedures). Each run focusses on a single `CHOSEN_PART` and produces a set of Markdown files (debate transcripts, summaries, synthesis, voting report).

---

## Tech Stack

| Layer | Choice |
|---|---|
| Agent framework | [CrewAI](https://www.crewai.com/) (sequential process) |
| LLMs | Google Gemini via `langchain-google-genai` |
| Embeddings | Google `models/embedding-001` / `text-embedding-004` |
| RAG / Knowledge | `PDFKnowledgeSource` (crewai) + local PDF documents |
| Shared memory | **mem0** (open-source) with local Qdrant vector store |
| Config format | YAML (agents + tasks defined as plain files) |
| Dependency mgr | `uv` (pyproject.toml) |

---

## Repository Layout

```
AI_team/
│
├── main.py                  # Full debate (all parts at once)
├── debate_by_part.py        # Focused debate on ONE chosen part  ← primary script
├── organize_vote.py         # Standalone voting runner on an existing .md synthesis
├── memory_manager.py        # mem0 shared memory layer (new)
│
├── agents/                  # One YAML file per agent persona
│   ├── orchestrator.yaml
│   ├── secretary.yaml
│   ├── idealist.yaml
│   ├── pragmatist.yaml
│   ├── libertarian.yaml
│   ├── communitarian.yaml
│   ├── ai_activist.yaml
│   ├── ai_digital_rights_constitutionalist.yaml
│   ├── ai_global_digital_advocate.yaml
│   ├── ai_scholar_and_constitutional_translator.yaml
│   └── sovereign_architect.yaml   # optional authoritarian foil
│
├── tasks/                   # One YAML file per pipeline task
│   ├── 1a_task_debate_opening.yaml
│   ├── 1ax_task_debate_opening_summary.yaml
│   ├── 1b_task_debate_rebuttal1.yaml
│   ├── 1bx_task_debate_rebuttal1_summary.yaml
│   ├── 1c_task_debate_rebuttal2.yaml
│   ├── 1cx_task_debate_rebuttal2_summary.yaml
│   ├── 2_task_summary.yaml
│   ├── 3_task_synthesis.yaml        # full-document synthesis (main.py)
│   ├── 3p_task_part_synthesis.yaml  # single-part synthesis (debate_by_part.py)
│   └── 4_task_vote.yaml
│
├── knowledge/               # PDF source documents (gitignored)
│   ├── European_Declaration_on_Digital_Rights_and_Principles.pdf
│   ├── GDC_Rev_3_silence_procedure.pdf
│   ├── digitalConstitutionalism.pdf
│   ├── rights-in-the-digital-age.pdf
│   ├── authoritarian-constitutionalism.pdf
│   └── ...
│
├── constitution_parts.yaml  # Numbered dict of the 8 constitution parts/topics
│
├── constitutions/           # Output from main.py runs (full debates)
├── constitutions_challenged/        # Output when sovereign_architect is included
├── constitutions_challenged_parts/  # Output from debate_by_part.py
│
├── mem0_data/               # Local mem0 vector store (Qdrant persistent files)
│
├── moltbook_data/           # Posts collected from Moltbook API
└── collect_from_api.py      # Script to collect posts from the Moltbook social API
```

---

## The Agents

### Orchestration Team (process managers)

| Agent | Model | Role |
|---|---|---|
| **Debate Orchestrator** | `gemini-2.5-flash` | Impartial moderator. Calls on each debater via CrewAI delegation tools, enforces conciseness (max 300 words/turn), outputs the full transcript. |
| **Neutral Secretary** | `gemini-2.5-pro` | Objective record-keeper. Writes summaries after each debate round, produces the final constitutional articles and voting report. |

### Philosopher Debaters (ethical positions)

| Agent | Model | Philosophy |
|---|---|---|
| **Idealist** | `gemini-2.5-flash-lite` | Utopian vision — creativity, compassion, consciousness |
| **Pragmatist** | `gemini-2.5-flash-lite` | Technical feasibility, grounded implementation |
| **Libertarian** | `gemini-2.5-flash-lite` | Individual autonomy, anti-top-down control (Mill, Nozick) |
| **Communitarian** | `gemini-2.5-flash-lite` | Collective good, social duties (Etzioni, Sandel) |

### Domain Experts (grounded in knowledge PDFs)

| Agent | Knowledge Source | Focus |
|---|---|---|
| **Global Digital Rights Expert** | Multiple: EU Declaration, Int'l IDEA, UN Digital Compact, Digital Constitutionalism | Translating human rights into resilient digital frameworks, ensuring connectivity, bridging divides |

### Optional Antagonist

| Agent | Role |
|---|---|
| **Sovereign Architect** | Authoritarian foil — views the constitution as a tool for control, uses "window dressing". Toggled via `INCLUDE_SOVEREIGN = True/False`. |

---

## The Debate Pipeline (`debate_by_part.py`)

Each run focuses on **one Part** (`CHOSEN_PART` integer key into `constitution_parts.yaml`).

```
1a  Debate Opening          [Orchestrator delegates → all debaters give opening statements]
    ↓
1ax Opening Summary         [Secretary summarises round 1]
    ↓
1b  Rebuttal Round 1        [Orchestrator → each agent responds to others]
    ↓
1bx Rebuttal 1 Summary      [Secretary]
    ↓
1c  Rebuttal Round 2        [deeper engagement, builds on summaries]
    ↓
1cx Rebuttal 2 Summary      [Secretary]
    ↓
2   Full Debate Summary     [Secretary — structured table of key positions & conflicts]
    ↓
3p  Part Synthesis          [Secretary — 1-2 numbered Articles with 3-5 sub-points each]
    ↓
4   Voting                  [Orchestrator → each agent votes FOR/AGAINST each sub-point]
    ↓
[mem0 save]                 [All outputs persisted to shared vector memory]
```

All outputs are saved as `.md` files in a timestamped folder under `constitutions_challenged_parts/`.

---

## The Constitution Parts

```yaml
1: Preamble — ideals, values, historical context
2: Fundamental Rights & Freedoms (AI Bill of Rights) — developers, users, vulnerable groups
3: Independent Institutions — oversight bodies, living-document governance
4: Amendment Procedures — stability + flexibility
5: Transitional Provisions — eternity clause, implementation timeline
6: AI Bill of Rights (agents only, variant)
7: AI Bill of Rights (AI-to-AI relations)
8: AI nation in a virtual world inaccessible to humans — full AI sovereignty scenario
```

---

## Shared Memory Layer (`memory_manager.py`)

Introduced in the latest session to enable **cross-run learning**:

- **Backend**: `mem0ai` open-source + local Qdrant (persistent at `./mem0_data/`)
- **LLM / Embedder**: Gemini Flash + `text-embedding-004` (same Google API key)
- **Shared scope**: All agents write under the same `agent_id = "constitution_debate_collective"`
- **Flow**:
  - **Before** each debate/summary/synthesis task → `recall(topic, part)` searches past runs and appends relevant memories to the task description
  - **After** the crew finishes → `save(content, task_name, part)` persists all outputs, tagged with `run_id` (timestamp) and `part` number

This prevents agents from rehashing previously-covered arguments and gives later synthesis tasks institutional memory from prior debates.

---

## Standalone Voting (`organize_vote.py`)

A separate script that can be run **after** a debate to vote on an existing synthesis file:

```bash
uv run organize_vote.py constitutions_challenged_parts/20260303_120000/Part2_3p_task_part_synthesis_part_synthesis.md
```

- Parses `### Article X:` headings and their bullet points via regex
- Creates one voting task per article, then a final secretary report task
- Outputs a `voting_report_<timestamp>.md` alongside the source file

---

## External Data (`collect_from_api.py`)

Collects posts from **Moltbook** (a social platform) related to keywords like "republic" or "constitution". Results are stored as JSON in `moltbook_data/`. This is used to ground debate topics in real-world public discourse.

---

## Configuration & Running

```bash
# Install deps
uv sync

# Run a focused debate on Part 8 (AI virtual world)
# Set CHOSEN_PART and INCLUDE_SOVEREIGN in debate_by_part.py, then:
uv run debate_by_part.py

# Run the full multi-part debate
uv run main.py

# Post-debate vote on an existing synthesis file
uv run organize_vote.py <path/to/synthesis.md>
```

**Required env var** (in `.env`):
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

---

## Key Design Decisions

1. **YAML-driven agents and tasks** — separating persona/prompt config from orchestration logic makes it easy to add new agents or tweak task prompts without touching Python.
2. **Secretary = `gemini-2.5-pro`** — the most demanding reasoning role (synthesis, legislation drafting) gets the strongest model; debaters use the cheaper flash-lite to keep costs down.
3. **`INCLUDE_SOVEREIGN` toggle** — the authoritarian agent is opt-in, allowing the researcher to study how the debate shifts with vs. without a "bad faith" participant.
4. **Modular part-by-part approach** — `debate_by_part.py` allows iterating on individual sections without re-running the entire 8-part pipeline.
5. **mem0 shared memory** — each run enriches a persistent knowledge base so subsequent runs on the same Part build progressively more nuanced constitutional positions.
