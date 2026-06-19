from __future__ import annotations

SOFTWARE_FEATURE = "software_feature"
PROCESS_IMPROVEMENT = "process_improvement"
OVERSIZED_REQUEST = "oversized_request"
AMBIGUOUS_REQUEST = "ambiguous_request"


CONCEPT_TERMS = {
    "google_oauth_success_flow": ("google", "oauth", "sign-in", "sign in", "login"),
    "server_side_provider_code_exchange": ("provider code", "authorization code", "code exchange", "server-side", "server side", "callback"),
    "google_email_user_mapping": ("google email", "existing user", "pending user", "map", "mapping"),
    "cancelled_or_rejected_error": ("cancelled", "canceled", "rejected", "clear error", "error"),
    "no_access_token_in_url": ("token", "url", "query parameter", "not exposed"),
    "login_flow": ("login", "sign in", "sign-in", "authenticated"),
    "session_or_token_handling": ("session", "jwt", "token"),
    "failure_handling": ("failed", "failure", "error"),
    "payment_provider_timeout": ("payment provider timeout", "provider timeout", "timeout"),
    "retry_message": ("retry message", "retry"),
    "same_checkout_attempt": ("same checkout attempt", "same attempt", "current checkout"),
    "duplicate_order_prevention": ("duplicate order", "not created twice", "duplicate submit", "idempotent"),
    "backend_calculated_totals": ("backend", "totals", "final price", "tax", "shipping", "discount"),
    "only_one_order_created": ("one order", "single order", "only one order"),
    "sprint_goal_before_selection": ("sprint goal", "before selecting", "before product backlog"),
    "product_backlog_items_support_goal": ("product backlog", "support", "sprint goal"),
    "sprint_backlog_includes_goal_items_plan": ("sprint backlog", "selected", "plan"),
    "capacity_and_definition_of_done_considered": ("capacity", "definition of done", "dod"),
    "notification_trigger": ("trigger", "event"),
    "channel": ("slack", "email", "in-app", "channel"),
    "payload_or_delivery": ("payload", "delivery", "sent"),
    "named_capability_splits": ("authentication", "billing", "admin dashboard", "notifications", "analytics", "profile management", "reporting"),
    "non_ready_parent": ("split", "not approved", "revision"),
    "clarification_questions": ("which", "what", "scenario"),
}


STRONG_DOMAIN_TERMS = {
    "checkout": ("checkout", "payment", "order", "cart", "coupon", "shipping", "inventory", "tax"),
    "notification": ("slack", "webhook", "email notification", "in-app notification", "notification payload"),
    "scrum": ("sprint goal", "product backlog", "sprint planning", "sprint backlog"),
    "auth": ("google oauth", "oauth", "jwt", "token", "login", "sign-in", "sign in", "password"),
}


DOMAIN_KEYWORDS = {
    "auth": (
        "login",
        "log in",
        "logout",
        "oauth",
        "google sign-in",
        "google sign in",
        "google login",
        "sign in",
        "sign-in",
        "signin",
        "password",
        "jwt",
        "token",
        "authenticated route",
        "authenticated session",
        "authentication",
        "account access",
    ),
    "checkout": (
        "checkout",
        "cart",
        "payment",
        "coupon",
        "order",
        "shipping",
        "tax",
        "inventory",
        "retry payment",
    ),
    "notification": (
        "slack",
        "email",
        "in-app notification",
        "in app notification",
        "webhook",
        "notification payload",
        "notification",
        "alert",
        "jira notification",
    ),
    "scrum": (
        "sprint planning",
        "sprint goal",
        "sprint backlog",
        "product backlog",
        "scrum team",
        "sprint retrospective",
        "definition of done",
        "facilitation",
    ),
}


DOMAIN_SOURCE_TERMS = {
    "auth": ("auth_context", "login", "oauth", "jwt", "token", "account"),
    "checkout": ("checkout", "cart", "payment", "order", "shipping", "tax", "inventory"),
    "notification": ("notification", "slack", "email", "webhook", "alert", "jira"),
    "scrum": ("scrum", "sprint", "backlog", "facilitation", "definition of done"),
}


GOOGLE_LOGIN_TERMS = ("login", "log in", "sign in", "sign-in", "signin")


SOURCE_MATCH_TERMS = {
    "auth_context": ("auth", "login", "logout", "oauth", "callback", "jwt", "token", "password", "session"),
    "checkout_context": ("checkout", "cart", "payment", "order", "coupon", "inventory", "shipping", "tax"),
    "notification_context": ("notification", "slack", "email", "webhook", "alert"),
    "sprint_policy": ("sprint", "capacity", "policy", "planning", "backlog"),
    "scrum_guide_2020": ("scrum", "sprint", "backlog", "definition of done", "scrum team"),
    "acceptance_criteria": ("acceptance", "criteria", "given", "when", "then"),
    "user_stories": ("user story", "user stories", "epic", "invest"),
}


PLANNER_EVIDENCE_TEMPLATES = {
    "auth": {
        "user_story": "As a [User Role], I want to [perform authentication action], so that I can [achieve security/access goal].",
        "acceptance_criteria": [
            "Given [precondition], when [authentication action occurs], then [expected system behavior].",
            "Given [alternative precondition], when [authentication action occurs], then [expected alternative behavior].",
            "Given [failure condition], when [authentication fails], then [error handling behavior].",
        ],
        "tasks": {
            "be": ["Implement [backend authentication logic, session handling, error states]."],
            "fe": ["Add [frontend UI flow, error messages, and success redirects]."],
            "qa": ["Validate [happy path, failure paths, and security constraints]."],
        },
        "definition_of_done": [
            "All authentication acceptance criteria pass, including success and failure handling.",
            "Backend and frontend implementation for the authentication flow is complete.",
            "Unit tests and integration tests cover the authentication logic.",
            "QA evidence covers the defined authentication scenarios.",
        ],
    },
    "checkout": {
        "user_story": "As a [Shopper Role], I want to [perform checkout action], so that I can [achieve order goal].",
        "acceptance_criteria": [
            "Given [checkout precondition], when [checkout action occurs], then [expected system behavior].",
            "Given [totals calculation precondition], when [checkout action occurs], then [totals are calculated correctly].",
            "Given [checkout failure/edge case condition], when [action occurs], then [error handling behavior preventing duplicate/invalid orders].",
        ],
        "tasks": {
            "be": ["Implement [backend checkout processing, validation, and total calculation]."],
            "fe": ["Update [frontend checkout UI, error states, and totals display]."],
            "qa": ["Validate [checkout happy path, edge cases, and failure protection]."],
        },
        "definition_of_done": [
            "All checkout acceptance criteria pass, including validation and calculation logic.",
            "Backend and frontend implementation for the checkout flow is complete.",
            "QA evidence covers checkout scenarios and duplicate prevention.",
            "The completed story demonstrates successful checkout processing.",
        ],
    },
    "sprint": {
        "user_story": "As a [Scrum Role], I want to [improve a Scrum Event/Artifact], so that the Scrum Team can [achieve agile goal].",
        "acceptance_criteria": [
            "Given [Scrum Event starts], when [Scrum Team performs action], then [expected outcome].",
            "Given [Scrum Artifact is evaluated], when [Scrum Team performs action], then [alignment with goals].",
            "Given [Scrum Event is completed], when [output is produced], then [it includes required elements].",
        ],
        "tasks": {
            "be": ["Define [facilitation rules or backend tracking for Scrum Event/Artifact]."],
            "fe": ["Update [workspace or UI to capture Scrum Event/Artifact details]."],
            "qa": ["Validate [Scrum Team alignment, completeness, and Definition of Done]."],
        },
        "definition_of_done": [
            "The Scrum Event/Artifact improvement is defined and agreed upon.",
            "Selected items and outputs are validated against goals.",
            "Team capacity and Definition of Done are considered.",
            "The completed story demonstrates improved Scrum workflow.",
        ],
    },
    "general": {
        "acceptance_criteria": [],
        "tasks": {"be": [], "fe": [], "qa": []},
        "definition_of_done": [],
    },
}


PLANNER_CLARIFICATION_QUESTIONS = {
    "auth": [
        "Which user role or login flow should be improved, such as returning users, new users, password login, Google OAuth, or token refresh?",
        "What specific login outcome should change, such as sign-in speed, error handling, session expiry, security, or account mapping?",
        "Which success and failure scenarios must be covered before planning, such as failed login, expired token, logout, cancelled OAuth, or callback validation?",
    ],
    "checkout": [
        "Which checkout step should be improved, such as cart review, shipping address, payment confirmation, retry, or order creation?",
        "What specific checkout outcome should change, such as duplicate prevention, timeout handling, inventory mismatch, coupon warning, or backend totals?",
        "Which QA scenarios must be covered before planning, such as successful checkout, payment failure, duplicate submit, invalid coupon, or inventory mismatch?",
    ],
    "notification": [
        "Which notification channel or audience should be improved, such as Slack, email, in-app, team members, or customers?",
        "What workflow event should trigger the notification and what payload fields are required?",
        "Which delivery, failure, and audit scenarios must be validated before planning?",
    ],
    "scrum": [
        "Which Scrum event, artifact, or team workflow should be improved?",
        "What outcome should change for the Product Owner, Developers, Scrum Master, or stakeholders?",
        "Which Definition of Done, Sprint Goal, inspection, or adaptation criteria should be used to judge success?",
    ],
    "general": [
        "Which user, role, or stakeholder is affected by this request?",
        "What specific behavior or business outcome should change?",
        "Which constraints, success criteria, and failure cases must be clarified before sprint planning?",
    ],
}


DOMAIN_PROFILES = {
    "auth_google_login": {
        "story_type": SOFTWARE_FEATURE,
        "required_sources": ["auth_context"],
        "optional_sources": [],
        "required_concepts": [
            "google_oauth_success_flow",
            "server_side_provider_code_exchange",
            "google_email_user_mapping",
            "cancelled_or_rejected_error",
            "no_access_token_in_url",
        ],
        "forbidden_domains": ["checkout", "notification", "scrum"],
        "template_name": "auth_google_login",
    },
    "auth_general_login": {
        "story_type": SOFTWARE_FEATURE,
        "required_sources": ["auth_context"],
        "optional_sources": [],
        "required_concepts": ["login_flow", "session_or_token_handling", "failure_handling"],
        "forbidden_domains": ["checkout", "notification", "scrum"],
        "template_name": "auth_general_login",
    },
    "checkout_payment_retry": {
        "story_type": SOFTWARE_FEATURE,
        "required_sources": ["checkout_context"],
        "optional_sources": [],
        "required_concepts": [
            "payment_provider_timeout",
            "retry_message",
            "same_checkout_attempt",
            "duplicate_order_prevention",
            "backend_calculated_totals",
            "only_one_order_created",
        ],
        "forbidden_domains": ["auth", "notification", "scrum"],
        "template_name": "checkout_payment_retry",
    },
    "checkout_duplicate_payment": {
        "story_type": SOFTWARE_FEATURE,
        "required_sources": ["checkout_context"],
        "optional_sources": [],
        "required_concepts": [
            "payment_provider_timeout",
            "retry_message",
            "same_checkout_attempt",
            "duplicate_order_prevention",
            "backend_calculated_totals",
            "only_one_order_created",
        ],
        "forbidden_domains": ["auth", "notification", "scrum"],
        "template_name": "checkout_payment_retry",
    },
    "notification": {
        "story_type": SOFTWARE_FEATURE,
        "required_sources": ["notification_context"],
        "optional_sources": [],
        "required_concepts": ["notification_trigger", "channel", "payload_or_delivery"],
        "forbidden_domains": ["auth", "checkout", "scrum"],
        "template_name": "notification",
    },
    "sprint_planning_process": {
        "story_type": PROCESS_IMPROVEMENT,
        "required_sources": ["scrum_guide_2020"],
        "optional_sources": ["sprint_policy"],
        "required_concepts": [
            "sprint_goal_before_selection",
            "product_backlog_items_support_goal",
            "sprint_backlog_includes_goal_items_plan",
            "capacity_and_definition_of_done_considered",
        ],
        "forbidden_domains": ["auth", "checkout", "notification"],
        "template_name": "sprint_planning_process",
    },
    "oversized_request": {
        "story_type": OVERSIZED_REQUEST,
        "required_sources": [],
        "optional_sources": ["scrum_guide_2020", "sprint_policy"],
        "required_concepts": ["named_capability_splits", "non_ready_parent"],
        "forbidden_domains": [],
        "template_name": "oversized_split",
    },
    "ambiguous_request": {
        "story_type": AMBIGUOUS_REQUEST,
        "required_sources": [],
        "optional_sources": [],
        "required_concepts": ["clarification_questions"],
        "forbidden_domains": [],
        "template_name": "clarification",
    },
    "unknown": {
        "story_type": SOFTWARE_FEATURE,
        "required_sources": [],
        "optional_sources": [],
        "required_concepts": [],
        "forbidden_domains": [],
        "template_name": "unknown",
    },
}


SPLIT_CAPABILITIES = (
    "authentication",
    "billing",
    "admin dashboard",
    "notifications",
    "analytics",
    "profile management",
    "reporting",
    "permissions",
    "audit logs",
    "crud operations",
    "management module",
    "tracking system",
    "delivery flow",
    "assignment logic",
    "creation process",
)


def profile_for_domain(domain: str) -> dict:
    return dict(DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["unknown"]))
