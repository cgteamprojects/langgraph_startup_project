from typing import TypedDict, List, Annotated
import operator
from pydantic import  Field


class ResearchState(TypedDict):
    task: dict
    initial_research: str = Field(..., description="Initial information requires for the writing.")
    sections: List[str]
    research_data: List[dict]
    # Report layout
    title: str
    headers: dict
    date: str
    table_of_contents: str
    introduction: str
    conclusion: str
    sources: List[str]
    report: str


