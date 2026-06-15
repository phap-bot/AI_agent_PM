import json
import sys
from ai_scrum_master.core.pipeline import generate_story_pipeline

# Fix Windows console unicode print error
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    result = generate_story_pipeline(
        requirement="Tập trung phân tích và viết Story cho tính năng này: Add authentication",
        n_results=5,
        allow_fallback_without_context=True
    )
    
    evaluation = result.get("evaluation", {})
    issues = evaluation.get("issues", [])
    
    print("STATUS:", evaluation.get("status"))
    print("ISSUES:", issues)
    print("PLANNER QUALITY:", result.get("story", {}).get("planner_quality"))

if __name__ == "__main__":
    main()
