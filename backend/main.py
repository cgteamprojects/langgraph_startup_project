from dotenv import load_dotenv
import sys
import os
import uuid

import asyncio
import json
from agent_core.agents.scope_agents.orchestrator import ChiefEditorAgent
#from gpt_researcher.utils.enum import Tone

# Run with LangSmith if API key is set
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
load_dotenv()

def open_task():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.dirname(os.path.realpath('__file__')))
    # Construct the absolute path to task.json
    print(current_dir)
    task_json_path = os.path.join(current_dir, './backend/agent_core/agents/scope_agents/task.json')
    
    with open(task_json_path, 'r') as f:
        task = json.load(f)

    if not task:
        raise Exception("No task found. Please ensure a valid task.json file is present in the multi_agents directory and contains the necessary task information.")

    # Override model with STRATEGIC_LLM if defined in environment
    strategic_llm = os.environ.get("STRATEGIC_LLM")
    if strategic_llm and ":" in strategic_llm:
        # Extract the model name (part after the first colon)
        model_name = strategic_llm.split(":", 1)[1]
        task["model"] = model_name
    elif strategic_llm:
        task["model"] = model_name

    return task

async def run_research_task(query, websocket=None, stream_output=None, tone=None, headers=None):
    task = open_task()
    task["query"] = query

    chief_editor = ChiefEditorAgent(task, websocket, stream_output, tone, headers)
    research_report = await chief_editor.run_research_task()

    if websocket and stream_output:
        await stream_output("logs", "research_report", research_report, websocket)

    return research_report

async def main():
    task = open_task()

    chief_editor = ChiefEditorAgent(task)
    research_report = await chief_editor.run_research_task(task_id=uuid.uuid4())

    return research_report

if __name__ == "__main__":
    asyncio.run(main())
    #await main()
