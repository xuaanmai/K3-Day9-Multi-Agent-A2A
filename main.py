import os
import json
import zipfile
from src.data_loader import OlistDataLoader
from src.agents import CoordinatorAgent, AgentTraceLogger

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    input_dir = os.path.join(base_dir, "input")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("--> Loading Olist Datasets...")
    loader = OlistDataLoader(data_dir)
    loader.load_data()
    print("--> Datasets Loaded Successfully.")

    coordinator = CoordinatorAgent(loader)
    logger = AgentTraceLogger()

    # Process all input cases EC_001.json to EC_050.json
    processed_count = 0
    for i in range(1, 51):
        case_file = f"EC_{i:03d}.json"
        input_path = os.path.join(input_dir, case_file)
        
        if not os.path.exists(input_path):
            print(f"Warning: Input file {case_file} not found.")
            continue

        with open(input_path, "r", encoding="utf-8") as f:
            case_input = json.load(f)

        output_data = coordinator.process_case(case_input, logger)

        output_path = os.path.join(output_dir, case_file)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        processed_count += 1

    print(f"--> Successfully processed {processed_count} cases into output/ directory.")

    # Write trace.jsonl
    trace_path = os.path.join(base_dir, "trace.jsonl")
    with open(trace_path, "w", encoding="utf-8") as f:
        for entry in logger.traces:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"--> Saved trace log to {trace_path} ({len(logger.traces)} entries).")

    # Create submission ZIP containing output/EC_001.json to output/EC_050.json
    zip_path = os.path.join(base_dir, "output.zip")
    with open(zip_path, "wb") as f_out:
        with zipfile.ZipFile(f_out, "w", zipfile.ZIP_DEFLATED) as zipf:
            for i in range(1, 51):
                case_file = f"EC_{i:03d}.json"
                file_in_output = os.path.join(output_dir, case_file)
                if os.path.exists(file_in_output):
                    zipf.write(file_in_output, arcname=f"output/{case_file}")

    print(f"--> Submission package created successfully: {zip_path}")

if __name__ == "__main__":
    main()
