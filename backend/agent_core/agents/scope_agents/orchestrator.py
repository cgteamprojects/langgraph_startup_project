import os
import time
import datetime
from langgraph.graph import StateGraph,MessagesState, END, START
# from langgraph.checkpoint.memory import MemorySaver
from utils.views import print_agent_output
from utils.utils import sanitize_filename
from IPython.display import Image, display
from memory.state import ResearchState

# Import agent classes
 
from typing import TypedDict, List, Annotated
import operator


 

class ChiefEditorAgent:
    """Agent responsible for managing and coordinating editing tasks."""

    def __init__(self, task: dict, websocket=None, stream_output=None, tone=None, headers=None):
        self.task = task
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.tone = tone
        self.task_id = self._generate_task_id()
        self.output_dir = self._create_output_directory()

    def _generate_task_id(self):
        # Currently time based, but can be any unique identifier
        return int(time.time())

    def _create_output_directory(self):
        output_dir = "./outputs/" + \
            sanitize_filename(
                f"run_{self.task_id}_{self.task.get('query')[0:40]}")

        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def _initialize_agents(self):
        return {
            "research": ResearchAgent(self.websocket, self.stream_output, self.tone, self.headers),
            "writer": WriterAgent(self.websocket, self.stream_output, self.headers),
           # "human": HumanAgent(self.websocket, self.stream_output, self.headers)
        }


    def _draw_workflow(self,workflow):

        try:
            display(Image(workflow.get_graph().draw_mermaid_png()))
        except Exception:
            # This requires some extra dependencies and is optional
            print("""""""""""""---------Exception----------""""""""""""")
            pass

    def _create_workflow(self, agents):
        workflow = StateGraph(ResearchState)

        # Add nodes for each agent
        workflow.add_node("browser", agents["research"].run)

        workflow.add_node("writer", agents["writer"].run)

        #workflow.add_node("human", agents["human"].review_plan)

        # Add edges
        self._add_workflow_edges(workflow)
        
         
        self._draw_workflow(workflow)
        return workflow

    def _add_workflow_edges(self, workflow):
        workflow.add_edge(START,"browser")
        workflow.add_edge('browser', "writer")
        workflow.add_edge('writer', END)

        # Add human in the loop
    ''' workflow.add_conditional_edges(
            'human',
            lambda review: "accept" if review['human_feedback'] is None else "revise",
            {"accept": "researcher", "revise": "planner"}
        )
    '''
    def init_research_team(self):
        """Initialize and create a workflow for the research team."""
        print("init_research_team")
        agents = self._initialize_agents()
        return self._create_workflow(agents)

    async def _log_research_start(self):
        message = f"Starting the research process for query '{self.task.get('query')}'..."
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "starting_research", message, self.websocket)
        else:
            print_agent_output(message, "MASTER")

    async def run_research_task(self, task_id=None):
        """
        Run a research task with the initialized research team.

        Args:
            task_id (optional): The ID of the task to run.

        Returns:
            The result of the research task.
        """
        research_team = self.init_research_team()
        chain = research_team.compile()

        await self._log_research_start()

        config = {
            "configurable": {
                "thread_id": task_id,
                "thread_ts": datetime.datetime.utcnow()
            }
        }
        print(config) 

        result = await chain.ainvoke({"task": self.task}, config=config)
        return result
