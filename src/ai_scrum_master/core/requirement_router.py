from __future__ import annotations

from typing import Any

from ai_scrum_master.core.domain_profiles import (
    DOMAIN_KEYWORDS,
    DOMAIN_PROFILES,
    GOOGLE_LOGIN_TERMS,
    OVERSIZED_CAPABILITIES,
    profile_for_domain,
)


def route_requirement(requirement: str) -> dict[str, Any]:
    text = " ".join(requirement.lower().split())
    words = text.split()

    oversized_hits = [term for term in OVERSIZED_CAPABILITIES if term in text]
    if len(oversized_hits) >= 3:
        return _route("oversized_request", f"Request names multiple capabilities: {', '.join(oversized_hits[:5])}.")

    if _is_ambiguous(text, words):
        return _ambiguous_route(text)

    # For requirements longer than a short sentence (>15 words), only route
    # to a specific domain if that domain keyword appears in the title
    # (first line) or first sentence — not just mentioned deep in the body.
    # This prevents tangential mentions of "notification", "login", etc.
    # from hijacking routing for a booking or general requirement.
    is_long = len(words) > 15
    # Extract the title/first line from the ORIGINAL text (before newlines were stripped)
    raw_lines = [line.strip().lower() for line in requirement.strip().splitlines() if line.strip()]
    first_line = raw_lines[0] if raw_lines else text[:100]
    # Also try first sentence (before first period)
    first_sentence = text.split(".")[0] if "." in text else first_line
    # Use the shorter of the two as the "primary context"
    primary_text = first_line if len(first_line) <= len(first_sentence) else first_sentence

    # Multi-domain conflict: if multiple unrelated domains match in a long
    # requirement, it's a general/cross-cutting requirement — route to unknown.
    if is_long:
        matched_domains = []
        if _has_auth(text): matched_domains.append("auth")
        if "checkout" in text or "payment" in text: matched_domains.append("checkout")
        if _has_notification(text): matched_domains.append("notification")
        if _has_sprint_planning(text): matched_domains.append("scrum")
        if len(matched_domains) >= 2 and not any(_has_domain_keyword(primary_text, d) for d in ["auth", "checkout", "notification", "scrum"]):
            return _route("unknown", f"Requirement mentions multiple domains ({', '.join(matched_domains)}) but none is the primary topic.")

    if _has_google_login(text):
        return _route("auth_google_login", "Requirement mentions Google sign-in/login and account access.")
    if _has_auth(text) and (not is_long or _has_auth(primary_text)):
        return _route("auth_general_login", "Requirement is about login/authentication without a Google-specific ask.")
    if "checkout" in text and (not is_long or "checkout" in primary_text):
        if "duplicate" in text or "twice" in text:
            return _route("checkout_duplicate_payment", "Requirement mentions checkout and duplicate order/payment prevention.")
        if "payment" in text or "provider timeout" in text or "retry payment" in text:
            return _route("checkout_payment_retry", "Requirement mentions checkout payment retry or provider timeout.")
    if _has_sprint_planning(text) and (not is_long or _has_sprint_planning(primary_text)):
        return _route("sprint_planning_process", "Requirement is about improving Sprint Planning and Sprint Goal definition.")
    if _has_notification(text) and (not is_long or _has_notification(primary_text)):
        return _route("notification", "Requirement mentions notification delivery or notification channels.")
    return _route("unknown", "No known domain matched deterministic routing rules.")


def _route(domain: str, reason: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = profile_for_domain(domain)
    if overrides:
        profile.update(overrides)
    return {
        "domain": domain,
        "story_type": profile["story_type"],
        "required_sources": list(profile["required_sources"]),
        "optional_sources": list(profile["optional_sources"]),
        "required_concepts": list(profile["required_concepts"]),
        "forbidden_domains": list(profile["forbidden_domains"]),
        "template_name": profile["template_name"],
        "profile": profile,
        "reason": reason,
        "reasoning": reason,
    }


def _ambiguous_route(text: str) -> dict[str, Any]:
    ambiguous_hint = _ambiguous_domain(text)
    profile_overrides = {}
    if ambiguous_hint.startswith("auth"):
        profile_overrides = {
            "required_sources": ["auth_context"],
            "forbidden_domains": DOMAIN_PROFILES["auth_general_login"]["forbidden_domains"],
            "template_name": "auth_clarification",
        }
    return _route(
        "ambiguous_request",
        "Requirement is too short or action-only, so it needs clarification before planning.",
        profile_overrides,
    )


def _is_ambiguous(text: str, words: list[str]) -> bool:
    starts_weak = any(text.startswith(prefix) for prefix in ("improve ", "fix ", "update ", "make better "))
    return len(words) <= 1 or (starts_weak and len(words) <= 4) or len(words) <= 2


def _ambiguous_domain(text: str) -> str:
    if _has_auth(text):
        return "auth_general_login"
    if "checkout" in text or "payment" in text:
        return "checkout_payment_retry"
    if _has_sprint_planning(text):
        return "sprint_planning_process"
    if _has_notification(text):
        return "notification"
    return "unknown"


def _has_google_login(text: str) -> bool:
    return "google" in text and any(term in text for term in GOOGLE_LOGIN_TERMS)


def _has_auth(text: str) -> bool:
    return _has_domain_keyword(text, "auth")


def _has_sprint_planning(text: str) -> bool:
    return _has_domain_keyword(text, "scrum")


def _has_notification(text: str) -> bool:
    return _has_domain_keyword(text, "notification")


def _has_domain_keyword(text: str, domain: str) -> bool:
    return any(term in text for term in DOMAIN_KEYWORDS[domain])
