import argparse
import json

from run import toolset_options
from src.processing.pass_k import calculate_pass_k, create_csv_pass_k, PassKResult
from src.processing.utils import csv_to_markdown
import os

PROCESSING_DIRNAME = 'processed'

def get_result_filepath(toolset: str, ix: int = None) -> str:
    if ix is not None:
        return f"results/{toolset}_toolset_{ix}.jsonl"
    else:
        return f"results/{toolset}_toolset.jsonl"

def toolset_name_shortcut(toolset_name: str) -> str:
    return ''.join(part[0] for part in toolset_name.split('_'))

def write_results_to_files(*, data: PassKResult, csv: str = None, run_id: str):
    present_tool_names = '_'.join(sorted(set(
        [toolset_name_shortcut(tool_name) for tool_name in data.keys()]
    )))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    processing_dir = os.path.join(base_dir, PROCESSING_DIRNAME)

    # Create processing directory if it doesn't exist
    if not os.path.exists(processing_dir):
        os.makedirs(processing_dir)

    json_filepath = os.path.join(processing_dir, f"{present_tool_names}_{run_id}.json")
    csv_filepath = os.path.join(processing_dir, f"{present_tool_names}_{run_id}.csv")

    written_files = []
    
    with open(json_filepath, "w") as f:
        f.write(json.dumps(data, indent=2) + "\n")
        written_files.append(json_filepath)

    if (csv is not None):
        with open(csv_filepath, "w") as f:
            f.write(csv + "\n")
            written_files.append(csv_filepath)
    
    return written_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process result files, calculate pass^k")
    parser.add_argument(
        "--toolsets",
        nargs="+",
        choices=list(toolset_options),
        required=True,
        help=f"Specify one or more toolsets to process: {', '.join(toolset_options)}"
    )
    parser.add_argument(
        "--ix",
        type=int,
        default=None,
        help="Specify the index of results file to process (default: without index)"
    )

    args = parser.parse_args()
    run_id = f"run_{args.ix}" if bool(args.ix) else "run_0"

    processed_result: PassKResult = {}

    for toolset in args.toolsets:
        results_file = get_result_filepath(toolset, args.ix)

        if os.path.exists(results_file):
            print(f"- Processing results file: {results_file}")
            pass_hat_ks = calculate_pass_k(results_file)
            processed_result[toolset] = pass_hat_ks
        else:
            print(f"- Results file {results_file} does not exist. Skipping.")
    
    csv_results = create_csv_pass_k(processed_result, run_id=run_id)

    try:
        written_files = write_results_to_files(
            data=processed_result,
            csv=csv_results,
            run_id=run_id
)
        print("\n- Saved processed results to disk")
        for file in written_files:
            print(f"  {file}")
    except Exception as e:
        print(f"Error while saving to disk: {e}")
    finally:
        print("\n- Processed results -")
        print(csv_to_markdown(csv_results))

        

