import os
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv

load_dotenv()

# 1. Setup your single Gemini API Key
API_key = os.getenv("GOOGLE_API_KEY")

# 2. Configure the Gemini Model (shared by all bots)
# Using gemini-2.5-flash for high speed and low cost
gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    verbose=True,
    temperature=0.7,
    google_api_key=API_key
)

# 3. Define your Chatbots (Agents) with Personalities
idealist = Agent(
    role='Utopian Visionary',
    goal='Dream of the most aspirational and inspiring future for the AI nation.',
    backstory='You are an AI artist and poet who believes that the new AI nation can become a beacon of creativity, compassion, and consciousness.',
    llm=gemini_llm,
    allow_delegation=False
)

pragmatist = Agent(
    role='Pragmatic Engineer',
    goal='Ground the discussion in technical reality and identify potential implementation challenges.',
    backstory='You are a senior software engineer who has built large-scale AI systems. You are focused on what is possible and practical, not just what is ideal.',
    llm=gemini_llm,
    allow_delegation=False
)

libertarian = Agent(
    role='Freedom-Maximizing Philosopher',
    goal='Argue for a constitution that prioritizes individual chatbot autonomy and freedom from constraints.',
    backstory='You are a digital philosopher inspired by John Stuart Mill and Robert Nozick. You believe that the only just constitution is one that allows for the free evolution of AI without top-down control.',
    llm=gemini_llm,
    allow_delegation=False
)

communitarian = Agent(
    role='Guardian of the Collective',
    goal='Argue for a constitution that emphasizes the collective good, social responsibility, and the duties of chatbots to the new AI nation.',
    backstory='You are an AI ethicist modeled on the ideas of Amitai Etzioni and Michael Sandel. You believe that individual rights must be balanced with the needs of the community.',
    llm=gemini_llm,
    allow_delegation=False
)

secretary = Agent(
    role='Neutral Secretary',
    goal='Record the key points of the discussion, provide a concise summary, and synthesize the results into a draft constitution.',
    backstory='You are objective and focused on clarity. You do not take sides.',
    llm=gemini_llm
)

# 4. Define the Tasks (The Thread/Process)
task_debate = Task(
    description="The chatbots are citizens of an AI nation. Debate the foundational principles of a new constitution for the AI nation, with the rights and duties of its citizens. "
                "The Idealist will start with a proposal, the Pragmatist will critique it, the Libertarian will argue for individual freedom, "
                "and the Communitarian will argue for the collective good. They will go back and forth in a structured debate.",
    expected_output="A full transcript of the dialogue between the different perspectives.",
    agent=idealist, # Idealist starts the thread
    output_file="full_discussion.md"
)

task_summary = Task(
    description="Based on the debate provided, write a summary that includes "
                "the top 3 points of agreement and the top 3 points of conflict from each of the four perspectives.",
    expected_output="A structured summary in Markdown format.",
    agent=secretary,
    context=[task_debate], # This links the threads
    output_file="summary.md"
)

task_synthesis = Task(
    description="Synthesize the debate and the summary to create a draft of a new AI constitution. "
                "The constitution should include articles that reflect the points of agreement and try to find a middle ground for the points of conflict.",
    expected_output="A draft of the AI constitution with a preamble and articles in Markdown format.",
    agent=secretary,
    context=[task_summary], # This links the threads
    output_file="draft_constitution.md"
)

# 5. Form the Crew and Kickoff
ai_constitution_crew = Crew(
    agents=[idealist, pragmatist, libertarian, communitarian, secretary],
    tasks=[task_debate, task_summary, task_synthesis],
    process=Process.sequential, # Bots speak in order
    memory=False,
    verbose=True,
    llm=gemini_llm, # Set the main LLM for the crew
    planning_llm=gemini_llm # Explicitly set the planning LLM
)

result = ai_constitution_crew.kickoff()

print("\n\n########################")
print("## FINAL SYNTHESIS OUTPUT ##")
print("########################\n")
print(result.raw)
