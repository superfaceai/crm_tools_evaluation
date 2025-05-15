import abc
from pydantic import BaseModel
from enum import Enum
from typing import Any, Dict, List, Optional

class Task(BaseModel):
    name: str
    prompt: str
    outcome: str

class CrmStateEngagements(BaseModel):
    emails: List[Dict[str, Any]]
    notes: List[Dict[str, Any]]
    calls: List[Dict[str, Any]]
    meetings: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]

class CrmState(BaseModel):
    contacts: List[Dict[str, Any]]
    companies: List[Dict[str, Any]]
    deals: List[Dict[str, Any]]
    engagements: CrmStateEngagements

class Model(str, Enum):
    GPT_4o = "openai/gpt-4o"
    GPT_4o_MINI = "openai/gpt-4o-mini"
    #CLAUDE_35 = "anthropic/claude-3.5"
    #CLAUDE_37 = "anthropic/claude-3.7"
    #GEMINI_20 = "google/gemini-2.0"

class Verdict(BaseModel):
    reasoning: str
    verdict: bool
    confidence: float # for fun to see how it estimates the confidence of the answer

class SolveResult(BaseModel):
    task: Task
    model: Model
    seed: Optional[int] = None
    messages: List[Dict[str, Any]]
    info: Dict[str, Any]
    trial_idx: Optional[int] = None
    trials_count: Optional[int] = None
    crm_state: Optional[CrmState] = None
    error: Optional[str] = None
    verdict: Optional[Verdict] = None

class Agent(abc.ABC):
    @abc.abstractmethod
    def solve(
        self, task: Task, max_num_steps: int = 30
    ) -> SolveResult:
        raise NotImplementedError

class Tool(abc.ABC):
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], handler: callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

    def __repr__(self):
        return f"Tool(name={self.name}, description={self.description})"
    
    def json_schema_dump(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
    
    async def run(self, arguments: Dict[str, Any]):
        return await self.handler(arguments)

class Toolset:
    name: str
    tools: List[Tool]

    def __init__(self, name: str, tools: List[Tool]):
        self.name = name
        self.tools = tools

    def __getitem__(self, item):
        for tool in self.tools:
            if tool.name == item:
                return tool
        raise KeyError(f"Tool {item} not found.")
    
    def __iter__(self):
        return iter(self.tools)
    
    def __len__(self):
        return len(self.tools)
