import json
from litellm import completion
from pydantic import ValidationError
from .shared import SolveResult, Model, Verdict

class Evaluator:
    def eval(self, result: SolveResult) -> Verdict:
        outcome = result.task.outcome
        crm_state = result.crm_state.model_dump_json(indent=2) if result.crm_state else "null"
        tool_calls = []
        for message in result.messages:
            if message['role'] == "assistant" and message['tool_calls']:
                for tool_call in message['tool_calls']:
                    tool_calls.append(tool_call)
        tool_calls = json.dumps(tool_calls, indent=2)
        final_response = result.messages[-1]['content']

        messages = [
            {
                "role": "system",
                "content": "\n".join([
                    "You are an evaluator."
                    "Based on the provided CRM STATE and OUTCOME DEFINITION, decide if the outcome is met.",
                    "CRM STATE has highest priority.",
                    "TOOL CALLS contains actions made to reach CRM STATE." 
                    "Use FINAL RESPONSE and TOOL CALLS to help to decide when not certain from CRM STATE.",
                ])
            },
            {
                "role": "user",
                "content": "\n".join([
                    "OUTCOME DEFINITION:",
                    outcome,
                    "TOOL CALLS:",
                    tool_calls,
                    "CRM STATE:",
                    str(crm_state),
                    "FINAL RESPONSE:",
                    final_response
                ])
            }
        ]

        response = completion(
            model=Model.GPT_4o,
            messages=messages,
            temperature=0,
            response_format=Verdict
        )
        
        try:
            result = response.choices[0].message.content
            verdict = Verdict.model_validate(json.loads(result))
            return verdict
        except ValidationError as e:
            print(f"Error validating response: {e}")
            return Verdict(reasoning="Error validating response", verdict=False, confidence=1.0)
        except Exception as e:
            print(f"Error: {e}")
            return Verdict(reasoning="Error during evaluation", verdict=False, confidence=1.0)
