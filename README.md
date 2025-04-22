## CRM Tools Evaluation

The goal of this repository is to compare different tools collections for Agents to work with CRMs.

Goal and how in points (TBD writing after numbers):
- Evaluate minimalistic agent to see effect of tools on performance
- Compare different models to eliminate model effect
- Focus to pass^k measuring consistency (pass hat k) [^2] metric
- Validating state in the HubSpot
- API mocking not possible, agent actions (different steps, order, ...)
- If the desired result is met, is evaluated by LLM.

**Toolsets:**
- Superface Tools
- Superface Specialist
- Cursor generated
- Composio
- __Later:__
  - Arcade (HubSpot not supported yet)
  - Zapier
  - Nango

## Setup
- Create Private App in Hubpot with all CRM scopes and `sales-email-read` scope
- Copy `.env.example` to `.env` and fill in the values
- Create a new virtual environment
    ```bash
    uv venv --python 3.12
    ```
- Install dependencies 
    ```bash
    uv pip install .
    ```

## Run

```bash
python run.py --toolsets superface
```

## Similar Benchmarks 

[^1] Gorilla: Large Language Model Connected with Massive APIs https://arxiv.org/abs/2305.15334
[^2] τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains https://arxiv.org/abs/2406.12045
[^3] AgentBench: Evaluating LLMs as Agents https://arxiv.org/abs/2308.03688 
[^4] CRMArena: Understanding the Capacity of LLM Agents to Perform Professional CRM Tasks in Realistic Environments https://arxiv.org/abs/2411.02305
