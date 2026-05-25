# Auth Context

The product uses JWT-based authentication for API sessions.

Current auth architecture:
- Backend owns login, logout, token refresh, and OAuth callback endpoints.
- Frontend has a login page, authenticated routes, and token storage logic.
- QA validates successful login, failed login, expired token, and logout behavior.

Google login constraints:
- OAuth callback must exchange the provider code server-side.
- Backend must map the Google email to an existing user or create a pending user record.
- Frontend must show a clear error if Google authentication is cancelled or rejected.
- Access tokens must not be exposed in URL query parameters.

Definition of done expectations:
- Unit tests cover token handling and callback validation.
- Integration tests cover the full login callback flow.
- QA has happy-path and failure-path scenarios.
