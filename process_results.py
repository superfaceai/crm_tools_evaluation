import json
from math import comb
from typing import List, Dict

from src.shared import SolveResult

def calculate_pass_k(results_file: str):
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
    pass_hat_ks: dict[int, float] = {}
    for task_name in n_per_task:
        n = n_per_task[task_name]
        c = c_per_task[task_name]
        for k in range(1, n+1):
            pass_hat_k = comb(c, k) / comb(n, k)
            if k in pass_hat_ks:
                pass_hat_ks[k] += pass_hat_k
            else:
                pass_hat_ks[k] = pass_hat_k
    for k in pass_hat_ks:
        pass_hat_ks[k] /= len(n_per_task)
            

    for k, pass_hat_k in pass_hat_ks.items():
        print(f"  k={k}: {pass_hat_k}")


if __name__ == "__main__":
    print("Pass ^ k for Superface tools")
    results_file = "results/superface_toolset.jsonl"
    calculate_pass_k(results_file)

    print("Pass ^ k for specialists")
    results_file = "results/superface_specialists_toolset.jsonl"
    calculate_pass_k(results_file)