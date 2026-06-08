from __future__ import annotations

import time

from ai_scrum_master.agents.crewai_contract import build_crewai_agent
from ai_scrum_master.core.agent_schemas import ResearchContextOutput, build_planning_brief, dump_model
from ai_scrum_master.core.config import AgentProfileConfig, TaskProfileConfig, get_settings
from ai_scrum_master.core.domain_profiles import SOURCE_MATCH_TERMS
from ai_scrum_master.core.logging import get_logger
from ai_scrum_master.core.quality_gate import evaluate_research_output, expected_relevance_for_requirement, normalize_source_name
from ai_scrum_master.retrieval.vector_store import get_chunks_by_filenames, search_context
from ai_scrum_master.tools.rag_tool import ProjectContextRagTool

logger = get_logger(__name__)


class ResearcherAgent:
    def __init__(self, profile: AgentProfileConfig | None = None, task_profile: TaskProfileConfig | None = None) -> None:
        self.settings = get_settings()
        self.profile = profile
        self.task_profile = task_profile
        self.llm = None

    def create_agent(self):
        from ai_scrum_master.core.llm_setup import build_llm
        if not self.llm:
            # Researcher cần phân tích tài liệu chuẩn xác (temperature = 0.2)
            self.llm = build_llm(temperature=0.2)
            
        role = self.profile.role if self.profile else "Research Context Specialist"
        goal = self.profile.goal if self.profile else "Retrieve relevant project context and confidence signals for planning."
        backstory = self.profile.backstory if self.profile else (
            "You analyze local vector-store evidence, keep only documentation-grounded context, "
            "and return a planning brief with confidence warnings."
        )
        return build_crewai_agent(role=role, goal=goal, backstory=backstory, tools=[ProjectContextRagTool()], verbose=True, llm=self.llm)

    def run(self, requirement: str, n_results: int = 5, route: dict | None = None, forced_context_docs: list[str] | None = None, project_id: str | None = None) -> dict:
        started_at = time.perf_counter()
        route = route or {}
        retrieval_query = self._build_retrieval_query(requirement, route)
        logger.info(
            "Research query started collection=%s n_results=%s top_k=%s requirement_length=%s retrieval_query_length=%s project_id=%s",
            self.settings.context_collection,
            n_results,
            self.settings.retrieval_context_top_k,
            len(requirement),
            len(retrieval_query),
            project_id,
        )
        try:
            # Fetch a larger pool to increase recall of required sources
            pool_size = max(20, n_results * 4)
            matches = search_context(
                query=retrieval_query,
                n_results=pool_size,
                collection_name=self.settings.context_collection,
                project_id=project_id,
            )
        except Exception as exc:
            latency_ms = self._elapsed_ms(started_at)
            logger.exception("Research query failed; continuing with empty context latency_ms=%s", latency_ms)
            return self._validate_output({
                "documents": [],
                "ids": [],
                "metadatas": [],
                "distances": [],
                "matches": [],
                "retrieved_sources": [],
                "selected_context_sources": [],
                "ignored_context_sources": [],
                "context_snippets": [],
                "planning_brief": self._build_planning_brief(requirement, [], "failed", 0.0),
                "retrieval_status": "failed",
                "retrieval_threshold": self.settings.retrieval_min_score,
                "raw_match_count": 0,
                "confidence": 0.0,
                "quality_gate": evaluate_research_output(requirement=requirement, matches=[], k=n_results, route=route),
                "route": route,
                "required_sources": route.get("required_sources", []),
                "optional_sources": route.get("optional_sources", []),
                "missing_required_sources": route.get("required_sources", []),
                "missing_optional_sources": route.get("optional_sources", []),
                "latency_ms": latency_ms,
                "stage_latencies_ms": {"researcher_ms": latency_ms},
                "warnings": [
                    f"Context retrieval failed; planner should continue with explicit assumptions. Reason: {exc}"
                ],
            })

        # --- Forced context: fetch all chunks from imported files ---
        forced_matches = []
        if forced_context_docs:
            forced_matches = get_chunks_by_filenames(
                filenames=forced_context_docs,
                query=retrieval_query,
                n_results=n_results,
                collection_name=self.settings.context_collection,
                project_id=project_id,
            )
            logger.info(
                "Forced context injection forced_files=%s forced_chunks=%s",
                forced_context_docs, len(forced_matches),
            )

        # Simply take the top matches without filtering by project context template
        threshold_matches = self._relevant_threshold_matches(requirement, matches, route)
        relevant_matches = self._top_matches(threshold_matches, n_results)

        # Merge forced context at the top (deduplicate by id)
        if forced_matches:
            existing_ids = {m.get("id") for m in relevant_matches}
            merged = [m for m in forced_matches if m.get("id") not in existing_ids]
            relevant_matches = merged + relevant_matches
        documents = [match["document"] for match in relevant_matches]
        ids = [match["id"] for match in relevant_matches]
        metadatas = [match["metadata"] for match in relevant_matches]
        distances = [match["distance"] for match in relevant_matches]
        warnings: list[str] = []

        if relevant_matches:
            retrieval_status = "ok"
        elif matches:
            retrieval_status = "no_relevant_context"
            warnings.append(
                f"No retrieved context met relevance threshold {self.settings.retrieval_min_score}."
            )
        else:
            retrieval_status = "empty"
            warnings.append("No relevant project context found in ChromaDB.")

        confidence = self._estimate_confidence(relevant_matches)
        if confidence < 0.5:
            warnings.append("Retrieved context confidence is low; planner should state assumptions explicitly.")

        retrieved_sources = self._build_retrieved_sources(relevant_matches)
        
        # Method 4: Map-Reduce Context Summarization if context is too large
        total_chars = sum(len(source["excerpt"]) for source in retrieved_sources)
        if total_chars > 3000:
            logger.info("Context length (%s) exceeds 3000 chars, triggering LLM summarization...", total_chars)
            try:
                from ai_scrum_master.core.llm_setup import build_llm
                if not self.llm:
                    self.llm = build_llm()
                combined_text = "\n\n".join(f"[{s['source']}]: {s['excerpt']}" for s in retrieved_sources)
                summary_prompt = (
                    "Summarize the following project context specifically for the requirement. "
                    "Keep all business rules, constraints, API names, and definitions of done intact.\n\n"
                    f"Requirement: {requirement}\n\nContext:\n{combined_text}"
                )
                raw_summary = self.llm.call([{"role": "user", "content": summary_prompt}])
                # Replace the excerpts with the summarized version
                if retrieved_sources:
                    retrieved_sources[0]["excerpt"] = str(raw_summary).strip()
                    retrieved_sources = [retrieved_sources[0]]
                logger.info("Summarization successful, reduced to 1 summarized source.")
            except Exception as e:
                logger.warning("Summarization failed, falling back to raw context: %s", e)
                warnings.append("Context summarization failed, using raw context.")

        context_snippets = self._build_context_snippets(retrieved_sources)
        planning_brief = self._build_planning_brief(requirement, retrieved_sources, retrieval_status, confidence)
        quality_gate = evaluate_research_output(
            requirement=requirement,
            matches=relevant_matches,
            k=n_results,
            route=route,
        )
        if not quality_gate["passed"]:
            warnings.extend([f"Research quality gate failed: {failure}" for failure in quality_gate["failures"]])
        for source in retrieved_sources:
            logger.info(
                "Research evidence source=%s chunk=%s score=%s excerpt=%s",
                source["source"],
                source["chunk_index"],
                source["score"],
                source["excerpt"],
            )
        if matches and not relevant_matches:
            logger.info(
                "Research filtered all matches below threshold threshold=%s raw_matches=%s best_score=%s",
                self.settings.retrieval_min_score,
                len(matches),
                max(float(match.get("score") or 0.0) for match in matches),
            )

        latency_ms = self._elapsed_ms(started_at)
        logger.info(
            "Research query completed top_documents=%s raw_matches=%s confidence=%s warnings=%s retrieval_status=%s threshold=%s latency_ms=%s",
            len(documents),
            len(matches),
            confidence,
            len(warnings),
            retrieval_status,
            self.settings.retrieval_min_score,
            latency_ms,
        )
        return self._validate_output({
            "documents": documents,
            "ids": ids,
            "metadatas": metadatas,
            "distances": distances,
            "matches": relevant_matches,
            "retrieved_sources": retrieved_sources,
            "selected_context_sources": retrieved_sources,
            "ignored_context_sources": [],
            "context_snippets": context_snippets,
            "planning_brief": planning_brief,
            "retrieval_status": retrieval_status,
            "retrieval_threshold": self.settings.retrieval_min_score,
            "raw_match_count": len(matches),
            "confidence": confidence,
            "quality_gate": quality_gate,
            "route": route,
            "required_sources": route.get("required_sources", []),
            "optional_sources": route.get("optional_sources", []),
            "missing_required_sources": [],
            "missing_optional_sources": [],
            "latency_ms": latency_ms,
            "stage_latencies_ms": {"researcher_ms": latency_ms},
            "warnings": warnings,
        })

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, round((time.perf_counter() - started_at) * 1000))

    def _estimate_confidence(self, matches: list[dict]) -> float:
        if not matches:
            return 0.0

        scores = [float(match.get("score") or 0.0) for match in matches]
        best_score = max(scores) if scores else 0.0
        strong_matches = sum(1 for score in scores if score >= 0.6)

        if best_score >= 0.8 and strong_matches >= 2:
            return 0.9
        if best_score >= 0.65:
            return 0.7
        if best_score >= 0.4:
            return 0.5
        return 0.3

    def _relevant_threshold_matches(self, requirement: str, matches: list[dict], route: dict | None = None) -> list[dict]:
        expected_sources = set(expected_relevance_for_requirement(requirement, route))
        relevant_matches = []
        req_words = set(w for w in requirement.lower().split() if len(w) > 2)
        req_len = len(req_words)

        for match in matches:
            candidate = dict(match)
            source_name = self._normalized_source_name(candidate)
            
            score = float(candidate.get("score") or 0.0)
            vector_score = float(candidate.get("vector_score") or 0.0)
            
            # Method 3: Jaccard Overlap Re-ranking
            doc_words = set(w for w in str(candidate.get("document", "")).lower().split() if len(w) > 2)
            overlap = len(req_words & doc_words)
            jaccard = (overlap / req_len) if req_len > 0 else 0.0
            
            # Rerank by combining vector score and jaccard overlap
            final_score = (score * 0.8) + (jaccard * 0.2)
            candidate["score"] = round(final_score, 3)
            candidate["score_reason"] = "jaccard_rerank"
            
            # Boost score if this match comes from an expected required source
            if expected_sources and self._match_matches_expected(candidate, source_name, expected_sources):
                boosted = min(1.0, candidate["score"] + 0.15)
                candidate["score"] = round(boosted, 3)
                candidate["score_reason"] = "expected_source_boost"

            if float(candidate.get("score") or 0.0) >= self.settings.retrieval_min_score:
                relevant_matches.append(candidate)
        return relevant_matches

    def _normalized_source_name(self, match: dict) -> str:
        metadata = match.get("metadata") if isinstance(match.get("metadata"), dict) else {}
        return normalize_source_name(str(metadata.get("source") or metadata.get("file_name") or match.get("source", "")))

    def _source_matches_expected(self, source_name: str, expected_sources: set[str]) -> bool:
        if source_name in expected_sources:
            return True
        return any(source_name == expected.split("_", 1)[0] for expected in expected_sources)

    def _match_matches_expected(self, match: dict, source_name: str, expected_sources: set[str]) -> bool:
        if self._source_matches_expected(source_name, expected_sources):
            return True
        searchable = " ".join(
            str(value)
            for value in (
                source_name,
                match.get("document", ""),
                (match.get("metadata") if isinstance(match.get("metadata"), dict) else {}).get("source", ""),
            )
        ).lower()
        for expected in expected_sources:
            if any(term in searchable for term in SOURCE_MATCH_TERMS.get(expected, ())):
                return True
        return False

    def _build_retrieval_query(self, requirement: str, route: dict | None = None) -> str:
        query = " ".join(requirement.replace(",", " ").split())
        lower = query.lower()
        replacements = [
            ("as a returning user", "returning user"),
            ("as an existing user", "existing user"),
            ("as a user", "user"),
            ("i want to", ""),
            ("i want", ""),
            ("so that", ""),
        ]
        for old, new in replacements:
            lower = lower.replace(old, new)
        expanded = " ".join(lower.split())
        if any(term in expanded for term in ("login", "log in", "sign in", "signin", "logout", "password", "token", "jwt", "oauth", "authentication")):
            expanded = f"{expanded} authentication login logout oauth callback jwt token account session"
        if "google" in expanded and any(term in expanded for term in ("sign in", "signin", "login", "log in")):
            expanded = f"{expanded} google oauth authentication login callback jwt"
        if route:
            required_concepts = " ".join(str(item).replace("_", " ") for item in route.get("required_concepts", []))
            template_name = str(route.get("template_name", "")).replace("_", " ")
            expanded = " ".join(part for part in (expanded, template_name, required_concepts) if part)
        return expanded or requirement

    def _top_matches(self, matches: list[dict], limit: int) -> list[dict]:
        deduped = []
        seen = set()
        ranked_matches = sorted(matches, key=lambda item: float(item.get("score") or 0.0), reverse=True)
        for match in ranked_matches:
            metadata = match.get("metadata") if isinstance(match.get("metadata"), dict) else {}
            key = (
                metadata.get("source") or metadata.get("file_name") or match.get("id"),
                metadata.get("chunk_index", "?"),
                " ".join(str(match.get("document", "")).split())[:200],
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(match)
            if len(deduped) >= limit:
                break
        return deduped

    def _prefer_project_context(self, matches: list[dict]) -> list[dict]:
        # Disabled filtering to support custom uploaded files
        return matches

    def _source_name(self, match: dict) -> str:
        metadata = match.get("metadata") if isinstance(match.get("metadata"), dict) else {}
        return str(metadata.get("source") or metadata.get("file_name") or match.get("id") or "").lower()

    def _build_retrieved_sources(self, matches: list[dict]) -> list[dict]:
        sources = []
        for match in matches:
            metadata = match.get("metadata") if isinstance(match.get("metadata"), dict) else {}
            document = str(match.get("document", "")).strip()
            sources.append(
                {
                    "id": match.get("id") or "",
                    "source": metadata.get("source") or metadata.get("file_name") or match.get("id") or "unknown source",
                    "chunk_index": metadata.get("chunk_index", "?"),
                    "score": float(match.get("score") or 0.0),
                    "distance": match.get("distance"),
                    "excerpt": self._excerpt(document),
                }
            )
        return sources

    def _build_context_snippets(self, retrieved_sources: list[dict]) -> list[str]:
        return [
            f"[{index}] source={source['source']} chunk={source['chunk_index']} score={source['score']}: {source['excerpt']}"
            for index, source in enumerate(retrieved_sources, start=1)
        ]

    def _build_planning_brief(
        self,
        requirement: str,
        retrieved_sources: list[dict],
        retrieval_status: str,
        confidence: float,
    ) -> dict:
        return build_planning_brief(
            requirement=requirement,
            sources=retrieved_sources,
            retrieval_status=retrieval_status,
            confidence=confidence,
            planning_instruction=(
                "Use only usable_evidence excerpts as project documentation evidence. "
                "If evidence is empty or low confidence, state assumptions and avoid inventing business rules."
            ),
        )

    def _excerpt(self, document: str) -> str:
        normalized = " ".join(document.split())
        if len(normalized) <= self.settings.retrieval_excerpt_chars:
            return normalized
        return normalized[: self.settings.retrieval_excerpt_chars].rstrip() + "..."

    def _validate_output(self, payload: dict) -> dict:
        return dump_model(ResearchContextOutput.model_validate(payload))
