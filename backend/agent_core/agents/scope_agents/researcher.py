from colorama import Fore, Style
from ...utils.views import print_agent_output
from typing import Dict, List, Any
import asyncio
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
import PyPDF2
from ...models import llm


class ResearchAgent:
    def __init__(self, websocket=None, stream_output=None, tone=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}
        self.tone = tone
        
       

        # Define the tools
        @tool
        def read_local_files(path: str, file_types: List[str] = ["txt", "pdf", "docx"]):
            """Read local files from a specified path with given file types."""
            extracted_text = ""
            pdf_path='IIA_Financial_Services_Guide_Final.pdf'
            try:
                # Open the PDF file in binary reading mode
                with open(pdf_path, 'rb') as file:
                    # Create a PDF reader object
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    # Get the number of pages in the PDF
                    num_pages = len(pdf_reader.pages)
                    
                    # Extract text from each page
                    for page_num in range(num_pages):
                        # Get the page object
                        page = pdf_reader.pages[page_num]
                        
                        # Extract text from the page
                        page_text = page.extract_text()
                        
                        # Add the page text to the extracted text
                        extracted_text += page_text + "\n\n"
                        
                    return f'<Document name="{pdf_path}">\n{extracted_text}\n</Document>'
                    
            except FileNotFoundError:
                return f"Error: The file {pdf_path} was not found."
            except Exception as e:
                return f"Error: {str(e)}"
    
        
        @tool
        def organiser(files: List[Dict], query: str, structure: str = "default"):
            """Organize extracted file data into a structured format based on the query."""
            # In a real implementation, this would organize the data
            return {
                "organized_data": {
                    "sections": ["Introduction", "Analysis", "Conclusion"],
                    "content": {
                        "Introduction": "Introduction content based on files...",
                        "Analysis": "Analysis of the data...",
                        "Conclusion": "Conclusion based on analysis..."
                    }
                }
            }
        
        self.tools = [read_local_files, organiser]
        self.tool_node = ToolNode(tools=self.tools)
        
        # Create the LLM and bind tools to it
        self.llm = llm #ChatAnthropic(model="claude-3-haiku-20240307")  # Define the LLM
        self.model = self.llm.bind_tools(self.tools)
        

    async def run_initial_research(self, research_state: dict):
        """Run initial research using the LangGraph workflow"""
        task = research_state.get("task", {})
        query = task.get("query", "")
        
        # Log the beginning of research
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "initial_research", f"Running initial research on: {query}", self.websocket)
        else:
            print_agent_output(f"Running initial research on: {query}", agent="RESEARCHER")
        
        # Create initial state with a human message - not a dictionary
        messages = [
            HumanMessage(content=f"""
            Research the following query: {query}
            
            IMPORTANT: Follow these steps in order:
            1. First, use the read_local_files tool to gather information from files
            2. Then summarise the data found in those files
            """)
        ]
        
        # Execute the workflow and collect the final result
        final_result = await asyncio.to_thread(
            llm.invoke,  # Use self.model instead of undefined llm
            messages  # Pass messages directly, not wrapped in a dictionary
        )
        
        # Structure the results properly
        research_results = {
            "task": task,
            "initial_research": {
                "messages": messages + [final_result]  # Store both input and output messages
            }
        }
        print("pdf result" )
        print(final_result)
        return research_results

    async def run(self, query: str, research_report: str = "research_report",
                     parent_query: str = "", verbose=True, source="web", tone=None, headers=None):
        """Main research method"""
        
        # Create research state
        research_state = {
            "task": {
                "query": query,
                "report_type": research_report,
                "parent_query": parent_query,
                "verbose": verbose,
                "source": source,
                "local_path": "./data",
                "file_types": ["txt", "pdf", "docx"]
            }
        }
        
        # Run the research
        result = await self.run_initial_research(research_state)
        if result:
          report = result
        else:
          report = "Research completed but no final report was generated."
        
        print_agent_output(f"Running initial research on the following query: {query}", agent="RESEARCHER")
        print_agent_output(f"Running initial research : {result}")
        return report