#!/usr/bin/env python3
import os
import re
import yaml
import sys
import datetime
from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Variables
INCLUDE_SOVEREIGN = True # To include the sovereign architect, set to True



def load_agents(lite_llm, flash_llm, pro_llm):
    agents = {}
    if not os.path.exists("agents"):
        print("Error: 'agents' directory not found.")
        sys.exit(1)
        
    for filename in os.listdir("agents"):
        if filename.endswith(".yaml"):
            agent_name = filename.split(".")[0]
            with open(os.path.join("agents", filename), "r") as f:
                agent_details = yaml.safe_load(f)

            # Make Sovereign Architect optional
            if agent_name == "sovereign_architect" and not INCLUDE_SOVEREIGN:
                continue

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
                agents[agent_name] = Agent(**agent_details, llm=pro_llm, max_iter=50)
            elif agent_name == "orchestrator":
                agents[agent_name] = Agent(**agent_details, llm=flash_llm, max_iter=50)
            else:
                agents[agent_name] = Agent(
                    **agent_details, 
                    llm=lite_llm, 
                    knowledge_sources=knowledge_sources if knowledge_sources else None
                )
    return agents

def parse_articles(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
        
    with open(filepath, 'r') as f:
        content = f.read()
    
    # regex to find articles
    # Looking for ### Article X: Title or similar
    articles = re.findall(r'(### Article \d+:.*?)(?=\n### Article \d+:|\n## |\n---|\Z)', content, re.DOTALL)
    # If no ### articles, try ## articles as fallback
    if not articles:
        articles = re.findall(r'(## Article \d+:.*?)(?=\n## Article \d+:|\n## |\n---|\Z)', content, re.DOTALL)
        
    return [a.strip() for a in articles]

def main():
    if len(sys.argv) < 2:
        print("Usage: python organize_vote.py <path_to_constitution.md>")
        sys.exit(1)

    constitution_path = sys.argv[1]
    
    load_dotenv()
    API_key = os.getenv("GOOGLE_API_KEY")
    if not API_key:
        print("Error: GOOGLE_API_KEY not found in .env file.")
        sys.exit(1)

    # Use the same models as main.py
    # Note: gemini-2.5-* models are used matching user's existing setup
    lite_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.7, google_api_key=API_key)
    flash_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7, google_api_key=API_key)
    pro_llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.7, google_api_key=API_key)
    
    agents = load_agents(lite_llm, flash_llm, pro_llm)
    
    articles = parse_articles(constitution_path)
    if not articles:
        print("No articles found in the provided markdown file. Ensure articles start with '### Article X:' or '## Article X:'.")
        sys.exit(1)

    voting_tasks = []
    debaters_list = [name for name in agents.keys() if name not in ["orchestrator", "secretary"]]
    
    print(f"Organizing vote on {len(articles)} articles with {len(debaters_list)} agents...")

    for i, article in enumerate(articles):
        article_title = article.split('\n')[0].replace('###', '').replace('##', '').strip()
        task = Task(
            description=(
                f"Organize a formal vote on the following article: {article_title}.\n\n"
                f"Article Content:\n{article}\n\n"
                f"You must consult EACH of these agents: {', '.join(debaters_list)}.\n"
                "Each agent must provide:\n"
                "1. Their vote (FOR or AGAINST).\n"
                "2. A brief justification (1-2 sentences) based on their persona and knowledge base.\n\n"
                "Ensure you capture every agent's vote clearly in your output. Do not skip any agent."
            ),
            expected_output=f"A clear summary of votes (FOR/AGAINST) and justifications from all agents for '{article_title}'.",
            agent=agents["orchestrator"]
        )
        voting_tasks.append(task)

    # Secretary task for the final report
    report_task = Task(
        description=(
            "You are the secretary for the AI Constitution voting process. "
            "Your task is to compile a final report based on the voting results of all articles provided in the context.\n\n"
            "The report MUST follow this structure:\n"
            "1. **Detailed Voting Results**: For each article, list the article title followed by each agent's name, their vote (FOR/AGAINST), and their full justification/point of view in plain text.\n"
            "2. **Summary Voting Table**: At the very end, provide a single, concise Markdown table with exactly these columns:\n"
            "   - **Article**: The title of the article.\n"
            "   - **For**: Comma-separated list of agent names who voted FOR.\n"
            "   - **Against**: Comma-separated list of agent names who voted AGAINST.\n"
            "   Do NOT include any commentary, arguments, or extra columns in this summary table.\n\n"
            "Ensure the report is professional, objective, and accurately reflects all votes recorded by the orchestrator."
        ),
        expected_output="A complete voting report in Markdown with detailed results followed by a concise summary table.",
        agent=agents["secretary"],
        context=voting_tasks
    )

    # Form the Crew
    vote_crew = Crew(
        agents=list(agents.values()),
        tasks=voting_tasks + [report_task],
        process=Process.sequential,
        verbose=True,
        embedder = {
            "provider": "google-generativeai",
            "config": {
                "model": "models/embedding-001",
                "api_key": API_key,
                "task_type": "retrieval_document"
            }
        }
    )

    result = vote_crew.kickoff()
    
    # Save the report
    const_dir = os.path.dirname(constitution_path)
    # Extract timestamp from constitution filename (e.g., 20260307_110850)
    match = re.search(r'(\d{8}_\d{6})', os.path.basename(constitution_path))
    const_timestamp = match.group(1) if match else "unknown"
    output_filename = os.path.join(const_dir, f"voting_report_{const_timestamp}.md")
    
    # Ensure result is string
    report_content = str(result)
    
    # Human readable date
    nice_date = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    with open(output_filename, "w") as f:
        f.write("# AI Constitution Voting Report\n\n")
        f.write(f"**Vote Date:** {nice_date}\n")
        f.write(f"**Source Constitution:** {os.path.basename(constitution_path)}\n\n")
        f.write(report_content)
    
    print(f"\nVoting process completed successfully.")
    print(f"Final report saved to: {output_filename}")

if __name__ == "__main__":
    main()
