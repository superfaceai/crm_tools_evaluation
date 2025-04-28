import json
from math import comb
from typing import List, Union
import csv
import io

from src.shared import SolveResult

ROUND_TO_DECIMALS = 4
AVG_LITERAL = '_across_tasks'

type ToolsetName = str
type TaskName = str
type K = int
type ToolsetPassK = dict[
    Union[TaskName, str], # task name or `AVG_LITERAL`
    dict[K, float]
]

type PassKResult = dict[ToolsetName, ToolsetPassK]

def calculate_pass_k(results_file: str) -> ToolsetPassK:
    with open(results_file, 'r') as f:
        results: List[SolveResult] = [SolveResult.model_validate(json.loads(line)) for line in f.readlines()]

    n_per_task: dict[str, int] = {} # n - number of trials
    c_per_task: dict[str, int] = {} # c - number of successful trials
    for result in results:
        task_name = result.task.name
        if task_name not in n_per_task:
            n_per_task[task_name] = result.trials_count
        if task_name not in c_per_task:
            c_per_task[task_name] = 1 if result.verdict.verdict else 0
        else:
            c_per_task[task_name] += 1 if result.verdict.verdict else 0

    # pass^k
    pass_hat_ks: dict[str, dict[int, float]] = {}
    for task_name in n_per_task:
        if task_name not in pass_hat_ks:
            pass_hat_ks[task_name] = {}

        n = n_per_task[task_name]
        c = c_per_task[task_name]

        for k in range(1, n+1):
            pass_hat_k = comb(c, k) / comb(n, k)
            pass_hat_ks[task_name][k] = round(pass_hat_k, ROUND_TO_DECIMALS)

    # Calculate averages for each pass^k across all tasks
    n_of_tasks = len(pass_hat_ks)
    avgs_per_k = {
        k: round(sum(d[k] for d in pass_hat_ks.values()) / n_of_tasks, ROUND_TO_DECIMALS) 
            for k in next(iter(pass_hat_ks.values()))
    }

    pass_hat_ks[AVG_LITERAL] = avgs_per_k
    
    return pass_hat_ks

def create_csv_pass_k(results: PassKResult, *, run_id: str) -> str:
    # Collect all k's
    all_ks = set()
    for toolset_passk in results.values():
        for task_data in toolset_passk.values():
            all_ks.update(task_data.keys())
    all_ks = sorted(all_ks)

    # Prepare CSV header
    header = ['toolset', 'task'] + [f'k={k}' for k in all_ks] + ['run_id']

    # Create an in-memory file
    output = io.StringIO()
    writer = csv.writer(output)

    # Write to it
    writer.writerow(header)
    for toolset_name, toolset_passk in results.items():
        for task_name, k_dict in toolset_passk.items():
            row = [toolset_name, task_name] + [k_dict.get(k, '') for k in all_ks] + [run_id]
            writer.writerow(row)

    # Get CSV content as a string
    csv_content = output.getvalue()

    # Optional: don't forget to close the StringIO object when done
    output.close()

    return csv_content
