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
        "user_story": "As a returning user, I want to sign in with Google, so that I can access my account quickly without entering a password.",
        "acceptance_criteria": [
            "Given a returning user starts Google sign-in, when the Google OAuth callback succeeds, then the backend exchanges the provider code server-side and establishes a JWT-based API session.",
            "Given Google returns an email for the authenticated account, when the backend processes the callback, then it maps the email to an existing user or creates a pending user record.",
            "Given Google authentication is cancelled or rejected, when the frontend receives the failure outcome, then it shows a clear error and does not expose access tokens in URL query parameters.",
        ],
        "tasks": {
            "be": ["Implement Google OAuth callback handling, server-side provider-code exchange, user mapping, and JWT session issuance."],
            "fe": ["Add Google sign-in flow handling on the login page, including callback success and cancelled/rejected error states."],
            "qa": ["Validate Google login happy path, cancelled/rejected failure path, token handling, callback validation, and protected-route regression scenarios."],
        },
        "definition_of_done": [
            "All Google sign-in acceptance criteria pass, including callback success, failure handling, and token exposure constraints.",
            "Backend and frontend implementation for OAuth callback, JWT session handling, login UI, and error handling is complete.",
            "Unit tests cover token handling and callback validation, and integration tests cover the full login callback flow.",
            "QA evidence covers Google login happy-path and failure-path scenarios documented for authentication.",
        ],
    },
    "checkout": {
        "user_story": "As an authenticated shopper, I want to retry checkout payment after a provider timeout, so that I can complete checkout without creating duplicate orders.",
        "acceptance_criteria": [
            "Given a signed-in shopper is on the same checkout attempt and the payment provider times out, when the shopper retries payment, then the frontend shows a retry message and keeps the checkout attempt active.",
            "Given checkout totals are displayed for retry, when payment is retried, then the frontend uses backend-calculated final price, discount, tax, and shipping totals.",
            "Given the shopper retries payment after a provider timeout, when the backend processes the retry, then duplicate order protection ensures only one order is created.",
        ],
        "tasks": {
            "be": ["Implement retry-safe checkout payment handling that preserves the same checkout attempt, uses backend-calculated totals, and prevents duplicate order creation."],
            "fe": ["Show a payment-provider-timeout retry message while displaying backend-calculated checkout totals for the same checkout attempt."],
            "qa": ["Validate payment provider timeout retry, duplicate submit protection, backend totals display, and that only one order is created."],
        },
        "definition_of_done": [
            "All checkout retry acceptance criteria pass, including provider timeout retry, same checkout attempt handling, backend totals, duplicate order prevention, and only one order creation.",
            "Backend and frontend implementation for retry-safe checkout behavior is complete.",
            "QA evidence covers payment timeout retry, duplicate submit protection, backend totals display, and one-order creation.",
            "The completed story demonstrates that payment retry does not create duplicate orders when the provider times out.",
        ],
    },
    "sprint": {
        "user_story": "As a Scrum Master, I want to improve Sprint Planning, so that the Scrum Team can define a clear Sprint Goal before selecting Product Backlog items.",
        "acceptance_criteria": [
            "Given Sprint Planning starts, when the Scrum Team defines the Sprint Goal, then the goal is agreed before selecting Product Backlog items.",
            "Given Product Backlog items are candidates for the Sprint, when the Scrum Team selects work, then each selected item supports the Sprint Goal.",
            "Given Sprint Planning is completed, when the Sprint Backlog is created, then it includes the Sprint Goal, selected Product Backlog items, and a delivery plan that considers team capacity and Definition of Done.",
        ],
        "tasks": {
            "be": ["Define Sprint Planning facilitation rules for Sprint Goal agreement, Product Backlog item selection, capacity review, and Definition of Done consideration."],
            "fe": ["Update the Sprint Planning checklist or workspace to capture Sprint Goal, selected Product Backlog items, delivery plan, team capacity, and Definition of Done checks."],
            "qa": ["Validate the Sprint Planning process with the Scrum Team for Sprint Goal clarity, Product Backlog alignment, Sprint Backlog completeness, capacity, and Definition of Done coverage."],
        },
        "definition_of_done": [
            "The Sprint Goal is defined and agreed before selecting Product Backlog items.",
            "Selected Product Backlog items are validated as supporting the Sprint Goal.",
            "The Sprint Backlog includes the Sprint Goal, selected items, and a delivery plan.",
            "Team capacity and Definition of Done are considered during Sprint Planning validation.",
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


OVERSIZED_CAPABILITIES = (
    "full",
    "portal",
    "platform",
    "authentication",
    "billing",
    "admin dashboard",
    "notifications",
    "analytics",
    "profile management",
    "reporting",
    "permissions",
    "audit logs",
)


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
)


def profile_for_domain(domain: str) -> dict:
    return dict(DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES["unknown"]))
