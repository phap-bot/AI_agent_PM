import json
import argparse
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_chatml_prompt(requirement: str, context_documents: list[str]) -> str:
    """
    Tái tạo lại chính xác System Prompt và User Prompt giống như PlannerAgent đã dùng.
    (Giữ nguyên format để đảm bảo lúc Fine-tune model học đúng ngữ cảnh).
    """
    system_prompt = (
        "You are an expert AI Scrum Master and Technical Product Manager. "
        "Your task is to analyze requirements and generate a comprehensive, actionable sprint-ready user story in JSON format."
    )
    
    # Context section
    context_str = ""
    if context_documents:
        context_str = "Context Documents (Use this to understand constraints and system behavior):\n"
        for i, doc in enumerate(context_documents, 1):
            context_str += f"--- Document {i} ---\n{doc}\n\n"
    
    user_prompt = f"""Based on the provided requirement and context, generate a detailed user story following the exact JSON schema provided.

Requirement:
{requirement}

{context_str}

Respond ONLY with valid JSON. Do not include markdown blocks or any other text."""

    return system_prompt, user_prompt

def main():
    parser = argparse.ArgumentParser(description="Convert Raw Benchmark JSONL to ChatML format for Fine-tuning Qwen")
    parser.add_argument("--input", type=str, required=True, help="Path to the raw JSONL output from benchmark (e.g., val_report_mistral_raw.jsonl)")
    parser.add_argument("--output", type=str, default="planner_finetune_dataset.jsonl", help="Output ChatML JSONL file")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    output_path = Path(args.output)
    
    valid_samples = 0
    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:
        
        for line in infile:
            if not line.strip():
                continue
                
            record = json.loads(line)
            
            # 1. Trích xuất Input
            requirement = record.get("requirement", "")
            context = record.get("context", {})
            context_documents = context.get("documents", [])
            
            # 2. Trích xuất Output Vàng (Golden JSON)
            planner_output = record.get("planner_output", {})
            
            # Bỏ qua nếu data không đạt chuẩn READY
            if planner_output.get("planning_status") != "READY":
                continue
                
            # Xây dựng lại Prompt
            system_msg, user_msg = generate_chatml_prompt(requirement, context_documents)
            
            # Đóng gói JSON đầu ra thành string chuẩn
            assistant_msg = json.dumps(planner_output, ensure_ascii=False, indent=2)
            
            # 3. Tạo cấu trúc ChatML
            chatml_record = {
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg}
                ]
            }
            
            # Ghi vào file
            outfile.write(json.dumps(chatml_record, ensure_ascii=False) + "\n")
            valid_samples += 1

    logger.info(f"Successfully created fine-tuning dataset with {valid_samples} high-quality samples.")
    logger.info(f"Dataset saved to: {output_path.absolute()}")

if __name__ == "__main__":
    main()
