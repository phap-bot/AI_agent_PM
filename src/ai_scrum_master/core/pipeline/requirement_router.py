from __future__ import annotations

from typing import Any

from ai_scrum_master.core.config.domain_profiles import profile_for_domain


def build_route_from_classification(domain: str, story_type: str) -> dict[str, Any]:
    """Build a complete route configuration object based on LLM classification."""
    # Ensure domain is valid, fallback to unknown/general
    profile = profile_for_domain(domain)
    
    return {
        "domain": domain,
        "story_type": story_type, # Override the profile's default story type with the LLM's classification
        "required_sources": list(profile.get("required_sources", [])),
        "optional_sources": list(profile.get("optional_sources", [])),
        "required_concepts": list(profile.get("required_concepts", [])),
        "forbidden_domains": list(profile.get("forbidden_domains", [])),
        "template_name": profile.get("template_name", "unknown"),
        "profile": profile,
        "reason": f"Classified by LLM Analyzer as {story_type} in domain {domain}.",
        "reasoning": f"Classified by LLM Analyzer as {story_type} in domain {domain}.",
    }
