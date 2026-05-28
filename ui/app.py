from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path = [str(SRC_DIR), *[path for path in sys.path if path != str(SRC_DIR)]]

from ai_scrum_master.agents.crew import ScrumMasterCrew
from ai_scrum_master.core.config import get_settings
from ai_scrum_master.core.vector_store import get_collection
from ai_scrum_master.agents import crew as crew_module


st.set_page_config(page_title="AI Scrum Master", layout="wide")
st.title("AI Scrum Master Agent")

settings = get_settings()
collection_count = get_collection().count()
st.caption(
    f"Collection: {settings.context_collection} | Retrieval threshold: {settings.retrieval_min_score} | Chunks: {collection_count}"
)
st.sidebar.write(
    {
        "package_file": str(Path(crew_module.__file__).resolve()),
        "persist_dir": settings.chroma_persist_dir,
        "collection": settings.context_collection,
        "chunks": collection_count,
        "threshold": settings.retrieval_min_score,
    }
)

requirement = st.text_area("Requirement", height=140, placeholder="Describe the stakeholder request...")
n_results = st.number_input("Max retrieved chunks", min_value=1, max_value=10, value=5)
allow_fallback = st.checkbox("Allow fallback story when no retrieved context meets threshold")

if st.button("Generate", type="primary"):
    if not requirement.strip():
        st.warning("Enter a requirement first.")
    else:
        with st.spinner("Researching docs and planning story..."):
            result = ScrumMasterCrew().run(
                requirement=requirement,
                n_results=int(n_results),
                allow_fallback_without_context=allow_fallback,
            )

        context = result.get("context", {})
        st.subheader("Retrieved evidence")
        sources = context.get("retrieved_sources", [])
        if sources:
            st.dataframe(
                [
                    {
                        "source": source.get("source"),
                        "chunk": source.get("chunk_index"),
                        "score": source.get("score"),
                        "excerpt": source.get("excerpt"),
                    }
                    for source in sources
                ],
                use_container_width=True,
            )
        else:
            st.warning("No retrieved evidence met the configured threshold.")

        st.write(
            {
                "retrieval_status": context.get("retrieval_status"),
                "retrieval_threshold": context.get("retrieval_threshold"),
                "confidence": context.get("confidence"),
                "raw_match_count": context.get("raw_match_count"),
                "warnings": context.get("warnings", []),
            }
        )

        if result.get("story") is None:
            st.error("Planner was blocked because no relevant context was available.")
            st.subheader("Next steps")
            for step in result.get("next_steps", []):
                st.write(f"- {step}")
        else:
            st.subheader("Story")
            st.json(result["story"])
            st.subheader("Evaluation")
            st.json(result.get("evaluation", {}))
