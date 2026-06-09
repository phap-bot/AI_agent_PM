import json
from ai_scrum_master.agents.researcher import ResearcherAgent

def main():
    print("Initializing ResearcherAgent...")
    agent = ResearcherAgent()
    agent.create_agent()
    
    # Requirement test
    requirement = "The user should be able to sign in using their Google account to access the dashboard."
    
    # Route simulation with expected_sources and metrics flag
    route = {
        "evaluate_metrics": True,
        "expected_sources": ["login_page", "oauth_handler", "user_profile"]
    }
    
    print("\n--- Running Researcher Agent ---")
    print(f"Requirement: {requirement}")
    
    # Run the agent
    result = agent.run(requirement=requirement, n_results=3, route=route)
    
    print("\n--- Output ---")
    qg = result.get("quality_gate", {})
    
    print("\n[Retrieval Metrics]")
    print(json.dumps(qg.get("metrics", {}), indent=2))
    
    print("\n[RAG Metrics (from Qwen2.5-Coder)]")
    print(json.dumps(qg.get("rag_metrics", {}), indent=2))
    
    print("\n[Planning Brief Extract]")
    print(str(result.get("planning_brief", {}).get("brief", ""))[:300] + "...")

if __name__ == "__main__":
    main()
