from ai_scrum_master.core.llm_setup import build_llm

llm = build_llm()
response = llm.call("Hom nay trời mưa không?")
print(response)