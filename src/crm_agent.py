import json
from litellm import completion
from typing import Any, Dict, List
from .shared import Agent, Model, Tool, SolveResult

class CRMAgent(Agent):
    instructions = (
        "You are a CRM agent. You can interact with HubSpot."
    )

    def __init__(self, *, model: Model, tools: list[Tool]):
        self.model = model
        self.tools = tools

    def solve(self, task, max_num_steps = 30):
        messages: List[Dict[str, Any]] = [
            { "role": "system", "content": CRMAgent.instructions },
            { "role": "user", "content": task.prompt }
        ]

        for _ in range(max_num_steps):
            res = completion(
                model=self.model,
                messages=messages,
                tools=[t.json_schema_dump() for t in self.tools],
                store=True
            )
            
            msg = res.choices[0].message.model_dump()
            messages.append(msg)

            # TODO: Calculate cost of each step

            if msg.get("tool_calls"):
                for tool_call in msg["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    tool_args = tool_call["function"]["arguments"]

                    tool = next(
                        (t for t in self.tools if t.name == tool_name), None
                    )
                    if tool:
                        tool_response = tool.run(tool_args)

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(tool_response),
                        })
                    else:
                        raise ValueError(f"Tool {tool_name} not found")

            else:
                # no more tool calls exiting
                break

        return SolveResult(
            model=self.model,
            task=task,
            messages=messages,
            info={}
        )
