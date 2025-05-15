from datetime import datetime as dt
import json5 as json
from ...utils.views import print_agent_output
import asyncio
from langchain_core.utils.json import parse_json_markdown
import json_repair
from ...models import llm



sample_json = """
{
  "table_of_contents": A table of contents in markdown syntax (using '-') based on the research headers and subheaders,
  "introduction": An indepth introduction to the topic in markdown syntax and hyperlink references to relevant sources,
  "conclusion": A conclusion to the entire research based on all research data in markdown syntax and hyperlink references to relevant sources,
  "sources": A list with strings of all used source links in the entire research data in markdown syntax and apa citation format. For example: ['-  Title, year, Author [source url](source)', ...]
}
"""


class WriterAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers

    def get_headers(self, research_state: dict):
        return {
            "title": research_state.get("title"),
            "date": "Date",
            "introduction": "Introduction",
            "table_of_contents": "Table of Contents",
            "conclusion": "Conclusion",
            "references": "References",
        }

    async def write_sections(self, research_state: dict):
        query = research_state.get("title")
        data = research_state.get("research_data")
        task = research_state.get("task")
        follow_guidelines = task.get("follow_guidelines")
        guidelines = task.get("guidelines")
        sections = research_state.get("sections")

            

        print("Query:", query)
        print("Data:", data)
        print("Task:", task)
        print("Follow Guidelines:", follow_guidelines)
        print("Guidelines:", guidelines)
        
        prompt = [
            {
                "role": "system",
                "content": "You are a research writer. Your sole purpose is to write a well-written "
                "research reports about a "
                "topic based on research findings and information.\n ",
            },
            {
                "role": "user",
                "content": f"Today's date is {dt.now().strftime('%d/%m/%Y')}\n."
                f"Query or Topic: {query}\n"
                f"Research data: {str(data)}\n"
                f"Your task is to write an in depth, well written and detailed "
                f"introduction and conclusion to the research report based on the provided research data. "
                f"Do not include headers in the results.\n"
                f"You MUST include any relevant sources to the introduction and conclusion as markdown hyperlinks -"
                f"For example: 'This is a sample text. ([url website](url))'\n\n"
                f"{f'You must follow the guidelines provided: {guidelines}' if follow_guidelines else ''}\n"
                f"You MUST return nothing but a JSON in the following format (without json markdown):\n"
                f"{sample_json}\n\n",
            },
        ]
        
        ai_message_response = await asyncio.to_thread(llm.invoke, prompt)
        
        # Extract content from AIMessage and parse JSON
        try:
            # If AIMessage has a 'content' attribute
            if hasattr(ai_message_response, 'content'):
                content_str = ai_message_response.content
            # If AIMessage is string-like
            elif isinstance(ai_message_response, str):
                content_str = ai_message_response
            else:
                # Default to string representation
                content_str = str(ai_message_response)
                
            # Try to parse the JSON using json_repair
            parsed_response = json_repair.loads(content_str)
            
            # If parsing failed or didn't return a dict, try parse_json_markdown
            if not isinstance(parsed_response, dict):
                parsed_response = parse_json_markdown(content_str, parser=json_repair.loads)
                
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            # Fallback to empty dictionary with error message
            parsed_response = {
                "table_of_contents": "Error parsing response",
                "introduction": f"Error parsing LLM response: {str(e)}",
                "conclusion": "Error parsing response",
                "sources": []
            }
        
        print("-------------------start : writer response-------------------")
        print(ai_message_response)
        print("-------------------end : writer response-------------------")
        print("-------------------start : writer prompt-------------------")
        print(prompt)
        print("-------------------end : writer prompt-------------------")
        
        return parsed_response

    async def revise_headers(self, task: dict, headers: dict):
        prompt = [
            {
                "role": "system",
                "content": """You are a research writer. 
                Your sole purpose is to revise the headers data based on the given guidelines.""",
            },
            {
                "role": "user",
                "content": f"""Your task is to revise the given headers JSON based on the guidelines given.
                You are to follow the guidelines but the values should be in simple strings, ignoring all markdown syntax.
                You must return nothing but a JSON in the same format as given in headers data.
                Guidelines: {task.get("guidelines")}\n
                Headers Data: {headers}\n""",
            },
        ]

        ai_message_response = await asyncio.to_thread(llm.invoke, prompt)
        
        # Extract content from AIMessage and parse JSON
        try:
            # If AIMessage has a 'content' attribute
            if hasattr(ai_message_response, 'content'):
                content_str = ai_message_response.content
            # If AIMessage is string-like
            elif isinstance(ai_message_response, str):
                content_str = ai_message_response
            else:
                # Default to string representation
                content_str = str(ai_message_response)
                
            # Try to parse the JSON 
            parsed_response = json_repair.loads(content_str)
            
            # If parsing failed or didn't return a dict, try parse_json_markdown
            if not isinstance(parsed_response, dict):
                parsed_response = parse_json_markdown(content_str, parser=json_repair.loads)
                
            return {"headers": parsed_response}
            
        except Exception as e:
            print(f"Error parsing JSON response for headers: {e}")
            # Return original headers as fallback
            return {"headers": headers}

    async def run(self, research_state: dict):
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "writing_report",
                f"Writing final research report based on research data...",
                self.websocket,
            )
        else:
            print_agent_output(
                f"Writing final research report based on research data...",
                agent="WRITER",
            )
        print("Writer STATE : ")    
        print(research_state)    
        
        research_layout_content = await self.write_sections(research_state)
        print("000000000000")    

        if research_state.get("task").get("verbose"):
            if self.websocket and self.stream_output:
                research_layout_content_str = json.dumps(
                    research_layout_content, indent=2
                )
                await self.stream_output(
                    "logs",
                    "research_layout_content",
                    research_layout_content_str,
                    self.websocket,
                )
            else:
                print_agent_output(research_layout_content, agent="WRITER")

        headers = self.get_headers(research_state)
        print("---------HEADER-----------")    
        print(headers)    

        if research_state.get("task").get("follow_guidelines"):
            if self.websocket and self.stream_output:
                await self.stream_output(
                    "logs",
                    "rewriting_layout",
                    "Rewriting layout based on guidelines...",
                    self.websocket,
                )
            else:
                print_agent_output(
                    "Rewriting layout based on guidelines...", agent="WRITER"
                )
            headers_result = await self.revise_headers(
                task=research_state.get("task"), headers=headers
            )
            headers = headers_result.get("headers")
        print("Write Agent END")    

        # Now research_layout_content is a dictionary, so this will work
        return {**research_layout_content, "headers": headers}