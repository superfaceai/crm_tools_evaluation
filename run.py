import os
import json
from dotenv import load_dotenv
from superface import Superface
from superface.client.superface import SuperfaceAPI
from composio import ComposioToolSet
from datetime import datetime
from typing import List, Optional
from src.reset_hubspot import reset_hubspot
from src.shared import Model, Task, Tool, Toolset, SolveResult
from src.crm_agent import CRMAgent
from src.dump_hubspot import dump_hubspot
from src.evaluator import Evaluator

load_dotenv()
def create_empty_toolset() -> Toolset:
    return Toolset(
        name="Empty Toolset",
        tools=[]
    )

def create_superface_toolset() -> Toolset:
    superface = Superface(api_key=os.getenv("SUPERFACE_API_KEY"))
    sf_tools = superface.get_tools(user_id="benchmark")
    return Toolset(
        name="Superface Toolset",
        tools=[
            Tool(
                name=tool.name,
                description=tool.description,
                parameters=tool.input_schema_raw,
                handler=lambda arguments, tool=tool: tool.run(arguments),
            )
            for tool in sf_tools
        ]
    )

def create_superface_specialiasts_toolset() -> Toolset:
    superface = SuperfaceAPI(api_key=os.getenv("SUPERFACE_API_KEY"), base_url="https://pod.superface.ai")
    specialist_fd = superface.get(path='/api/specialists/hubspot', user_id="benchmark")

    return Toolset(
        name="Superface Specialists Toolset",
        tools=[
            Tool(
                name=specialist_fd['name'],
                description=specialist_fd['description'],
                parameters=specialist_fd['parameters'],
                handler=lambda arguments: superface.post(path='/api/specialists/hubspot', data=json.loads(arguments), user_id="benchmark"),
            )
        ]
    )

def create_composio_toolset() -> Toolset:
    toolset = ComposioToolSet(api_key=os.getenv("COMPOSIO_API_KEY"))
    print(f"Toolset: {toolset}")

def load_tasks(slice: Optional[slice] = None) -> List[Task]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tasks_file = os.path.join(base_dir, "./data/tasks.jsonl")
    with open(tasks_file, "r") as f:
        tasks_data = [json.loads(line) for line in f.readlines()]
    tasks = []
    for task in tasks_data:
        tasks.append(Task(**task))
    if slice:
        tasks = tasks[slice]
    return tasks

def solve_task(*, task: Task, toolset: Toolset, model: Model, trials_count: int) -> List[SolveResult]:
    print(f"🛠️ Task {task.name}")

    agent = CRMAgent(
        model=model,
        tools=toolset
    )

    results: List[SolveResult] = []
    for i in range(1, trials_count+1):
        try:
            print("🧹 Resetting CRM...")
            reset_hubspot()

            print(f"🤖 Run {i}/{trials_count}")
            result = agent.solve(task=task)
            
            result.trial_idx = i
            result.trials_count = trials_count

            print("🗂️ Dumping CRM state...")
            result.crm_state = dump_hubspot()

            print("🧪 Evaluating task...")
            result = evelauate_task(result=result)

            print(f"🔨 Verdict: {'👍' if result.verdict.verdict else '👎'}")
            print(f"      Reasoning: {result.verdict.reasoning}")
            print(f"      Confidence: {result.verdict.confidence}")

            results.append(result)
        except Exception as e:
            print(f"❌ Failed attempt: {e}")
            result = SolveResult(
                model=model,
                task=task,
                messages=[],
                info={},
                success=False,
                trial_idx=i,
                trials_count=trials_count,
                error=str(e)
            )
            continue

    return results

def evelauate_task(result: SolveResult) -> SolveResult:
    evaluator = Evaluator()
    verdict = evaluator.eval(result=result)
    result.verdict = verdict
    return result

def write_results_to_file(toolset: Toolset, results: List[SolveResult]):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    toolset_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in toolset.name.lower())
    results_file = os.path.join(base_dir, f"./results/{toolset_name}.jsonl")
    
    # Backup existing file if it exists
    if os.path.exists(results_file):
        backup_index = 1
        backup_file = os.path.join(base_dir, f"./results/{toolset_name}_{backup_index}.jsonl")
        while os.path.exists(backup_file):
            backup_index += 1
            backup_file = os.path.join(base_dir, f"./results/{toolset_name}_{backup_index}.jsonl")
        os.rename(results_file, backup_file)
    
    # Write results to the file
    with open(results_file, "w") as f:
        for result in results:
            f.write(json.dumps(result.model_dump()) + "\n")
        
def test_agent():
    toolset = create_superface_toolset()
    task = Task(name="Test Task", prompt="Create contact Test User test@example.net")
    agent = CRMAgent(
        model=Model.GPT_4o,
        tools=toolset
    )
    result = agent.solve(task=task)
    print(f"Result: {result}")

def dump_hubspot_state():
    hubspot_state = dump_hubspot()
    print(f"HubSpot State: {hubspot_state}")

def run(model = Model.GPT_4o, trials_count = 5):
    sf_toolset = create_superface_toolset()
    sf_specialist_toolset = create_superface_specialiasts_toolset()

    tasks = load_tasks()
    for toolset in [sf_toolset, sf_specialist_toolset]:
        results = []
        for task in tasks:
            result = solve_task(task=task, toolset=toolset, model=model, trials_count=trials_count)    
            results.extend(result)
        write_results_to_file(toolset, results)

if __name__ == "__main__":
    # test_agent()
    # reset_hubspot()
    # dump_hubspot_state()
    # create_composio_toolset()
    run(trials_count=1)
