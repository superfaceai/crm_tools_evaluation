import os
import json
from dotenv import load_dotenv
from superface import Superface
from superface.client.superface import SuperfaceAPI
from composio_openai import ComposioToolSet, Action
from typing import List, Optional, TextIO
from src.reset_hubspot import reset_hubspot
from src.shared import Model, Task, Tool, Toolset, SolveResult, Verdict
from src.crm_agent import CRMAgent
from src.dump_hubspot import dump_hubspot
from src.evaluator import Evaluator
from src.vibecode_toolset import create_vibecode_toolset
import argparse

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
        name="Superface Specialist Toolset",
        tools=[
            Tool(
                name=specialist_fd['name'],
                description=specialist_fd['description'],
                parameters=specialist_fd['parameters'],
                handler=lambda arguments: superface.post(path='/api/specialists/hubspot', data=json.loads(arguments), user_id="benchmark"),
            )
        ]
    )

def create_superface_dynamic_specialists_toolset() -> Toolset:
    superface = SuperfaceAPI(api_key=os.getenv("SUPERFACE_API_KEY"), base_url="https://pod.superface.ai")
    specialist_fd = superface.get(path='/api/specialists/dynamic/hubspot', user_id="benchmark")

    return Toolset(
        name="Superface Dynamic Specialist Toolset",
        tools=[
            Tool(
                name=specialist_fd['name'],
                description=specialist_fd['description'],
                parameters=specialist_fd['parameters'],
                handler=lambda arguments: superface.post(path='/api/specialists/dynamic/hubspot', data=json.loads(arguments), user_id="benchmark"),
            )
        ]
    )

def create_composio_toolset() -> Toolset:
    toolset = ComposioToolSet(api_key=os.getenv("COMPOSIO_API_KEY"))

    tools = toolset.get_tools(
        # filtering by tags doesn't work: https://github.com/ComposioHQ/composio/issues/1548
        # apps=[App.HUBSPOT],
        # tags=[Tag.HUBSPOT_CORE, Tag.HUBSPOT_BASIC],
        actions=[
            Action.HUBSPOT_CREATE_CONTACT_OBJECT_WITH_PROPERTIES, 
            Action.HUBSPOT_CREATE_COMPANY_OBJECT, 
            Action.HUBSPOT_SEARCH_CONTACTS_BY_CRITERIA, 
            Action.HUBSPOT_SEARCH_COMPANY_OBJECTS,
            Action.HUBSPOT_CREATE_NEW_DEAL_OBJECT,
            Action.HUBSPOT_SEARCH_DEALS_BY_CRITERIA,
            Action.HUBSPOT_READ_PROPERTY_GROUPS_FOR_OBJECT_TYPE,
            Action.HUBSPOT_LIST_ASSOCIATION_TYPES,
            Action.HUBSPOT_CREATE_BATCH_OF_OBJECTS,
        ],
    )
    
    return Toolset(
        name="Composio Toolset",
        tools=[
            Tool(
                name=tool['function']['name'],
                description=tool['function']['description'],
                parameters=tool['function']['parameters'],
                handler=lambda arguments, tool=tool: toolset.execute_action(action=tool["function"]["name"], params=json.loads(arguments))
            )
            for tool in tools
        ]
    )
    

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

def solve_task(*, file: TextIO, task: Task, toolset: Toolset, model: Model, trials_count: int, seed: Optional[int] = None):
    agent = CRMAgent(
        model=model,
        tools=toolset
    )

    for i in range(1, trials_count+1):
        try:
            print(f"🛠️ Task {task.name} {i}/{trials_count}")

            print("🧹 Resetting CRM...")
            reset_hubspot()

            result = agent.solve(task=task, seed=seed)            
            result.trial_idx = i
            result.trials_count = trials_count

            print("🗂️ Dumping CRM state...")
            result.crm_state = dump_hubspot()

            print("🧪 Evaluating task...")
            result = evaluate_task(result=result)

            print(f"🔨 Verdict: {'👍' if result.verdict.verdict else '👎'}")
            print(f"      Reasoning: {result.verdict.reasoning}")
            print(f"      Confidence: {result.verdict.confidence}")

            write_result_to_file(file=file, result=result)
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
                error=str(e),
                verdict=Verdict(
                    verdict=False,
                    reasoning="Error during task execution",
                    confidence=1.0
                )
            )
            write_result_to_file(file=file, result=result)

def evaluate_task(result: SolveResult) -> SolveResult:
    evaluator = Evaluator()
    verdict = evaluator.eval(result=result)
    result.verdict = verdict
    return result

def open_results_file(toolset: Toolset) -> TextIO:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    toolset_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in toolset.name.lower())
    results_file = os.path.join(base_dir, f"./results/{toolset_name}.jsonl")
    results_dir = os.path.dirname(results_file)

    # Create results directory if it doesn't exist
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Backup existing file if it exists
    if os.path.exists(results_file):
        backup_index = 1
        backup_file = os.path.join(base_dir, f"./results/{toolset_name}_{backup_index}.jsonl")
        while os.path.exists(backup_file):
            backup_index += 1
            backup_file = os.path.join(base_dir, f"./results/{toolset_name}_{backup_index}.jsonl")
        os.rename(results_file, backup_file)
    
    return open(results_file, "w")

def write_result_to_file(file: TextIO, result: SolveResult):
    file.write(json.dumps(result.model_dump()) + "\n") 
        
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

def run(*, toolsets: List[Toolset], trials_count: int, model = Model.GPT_4o, seed: Optional[int] = None):    
    tasks = load_tasks()
    for toolset in toolsets:
        print(f"Running tasks for toolset: {toolset.name}")
        with open_results_file(toolset) as file:
            for task in tasks:
                solve_task(task=task, toolset=toolset, model=model, trials_count=trials_count, seed=seed, file=file)                

toolset_creators = {
    "superface": create_superface_toolset,
    "superface_specialist": create_superface_specialiasts_toolset,
    "superface_dynamic_specialist": create_superface_dynamic_specialists_toolset,
    "composio": create_composio_toolset,
    'vibecode': create_vibecode_toolset,
}

toolset_options = list(toolset_creators.keys())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CRM Tools Benchmark")
    parser.add_argument(
        "--toolsets",
        nargs="+",
        choices=toolset_options,
        required=True,
        help=f"Specify one or more toolsets to run: {', '.join(toolset_options)}"
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=5,
        help="Specify the number of trials to run (default: 5)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Specify the seed (default: None)"
    )
    args = parser.parse_args()

    selected_toolsets = [toolset_creators[toolset]() for toolset in args.toolsets]

    run(
        toolsets=selected_toolsets,
        trials_count=args.trials,
        seed=args.seed
    )
