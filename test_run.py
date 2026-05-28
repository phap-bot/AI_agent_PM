from ai_scrum_master.agents.crew import ScrumMasterCrew
import json

crew = ScrumMasterCrew()
res = crew.run("As a returning user, I want to sign in with Google so that I can access my account quickly without entering a password.", n_results=3)

print("=== STORY ===")
print(json.dumps(res["story"], indent=2, ensure_ascii=False))
print("\n=== EVALUATION ===")
print(json.dumps(res["evaluation"], indent=2, ensure_ascii=False))
