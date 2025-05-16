# CRM Tools Evaluation

This repository aims to systematically compare various tool collections that facilitate CRM (Customer Relationship Management) interactions by autonomous agents. The evaluation focuses on understanding how these toolsets affect agent performance in realistic CRM scenarios.

## Objectives

- **Evaluate Toolset Impact:** Assess how different CRM toolsets influence the performance of a minimalistic autonomous agent.
- **Consistency Measurement:** Apply and measure agent consistency using the Pass^k (pass hat k) metric. The Pass^k metric measures an agent's consistency by evaluating its success across multiple attempts to complete the same task, assessing whether the agent can consistently achieve the intended outcome within a set number (k) of attempts.
- **State Validation:** Confirm that the resulting CRM state within HubSpot aligns with expectations.
- **Real Interaction Evaluation:** Perform evaluations directly through the HubSpot API due to limitations in API mocking, as agent interactions may vary significantly in steps and execution order.
- **Result Validation:** Use an LLM-based evaluator to automatically verify if desired outcomes have been achieved.

## Toolsets Evaluated

Initial toolsets included in the evaluation:
- **Superface Tools:** Simplified interface for CRM API interactions.
- **Superface Specialist:** Specialized workflows built upon Superface for advanced use cases.
- **Superface Dynamic Specialist:** Self-navigating Superface agent for advanced use cases.
- **Vibe coded with Cursor:** AI-generated tools optimized for CRM interactions.
- **Composio:** Platform supporting multi-service integrations with emphasis on CRM processes.

## Environment Setup

### HubSpot Private App Setup

1. Create a new Private App in your HubSpot instance with the following scopes:
   - All CRM scopes
   - `sales-email-read`

2. Copy `.env.example` to `.env` and update it with your private app credentials.

### Python Environment

Set up a clean Python environment using Python 3.12:

```bash
uv venv --python 3.12
source .venv/bin/activate
```

Install the required dependencies:

```bash
uv pip install .
```

## Execution

Run the benchmark for specified toolsets:

- `--toolsets`: List of toolsets you want to run the benchmark for
- `--seed` *(optional)*: Specify a seed that is passed to LLMs (Default: none)
- `--trials` *(optional)*: Specify how many times each toolset<>task pair should run (Default: 5)
- `--crm`: hubspot or salesforce (Default: hubspot)

```bash
python run.py --toolsets superface superface_specialist superface_dynamic_specialist composio vibecode --seed 42 --trials 10
```

## Calculating Pass^k
To process recorded results and compute evaluation metrics, execute `process.py` script with:

- `--toolsets`: List of toolsets for which you want to evaluate the results
- `--ix` *(optional)*: Use to specify index of result files you want to analyze. This is for files in format `{toolname}_toolset_{ix}.jsonl` that are created when the benchmark is ran multiple times (Default: no index)

```bash
# Example: Evaluate all files under `{toolname}_toolset_2.jsonl`
python process.py --toolsets superface superface_specialist superface_dynamic_specialist composio vibecode --ix 2
```

## Reference Benchmarks

This evaluation is inspired by and comparable to the following benchmarks:

- [Gorilla: Large Language Model Connected with Massive APIs](https://arxiv.org/abs/2305.15334)
- [τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains](https://arxiv.org/abs/2406.12045)
- [AgentBench: Evaluating LLMs as Agents](https://arxiv.org/abs/2308.03688)
- [CRMArena: Understanding the Capacity of LLM Agents to Perform Professional CRM Tasks in Realistic Environments](https://arxiv.org/abs/2411.02305)

