from typing import Any, Optional
from fastapi import HTTPException, status

class BaseAppException(Exception):
    """Base exception for all custom application errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: Optional[Any] = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class LLMConnectionError(BaseAppException):
    """Raised when there is a connection issue with Ollama or LLM service."""
    def __init__(self, message: str = "Could not connect to the LLM service", details: Optional[Any] = None):
        super().__init__(message=message, code="LLM_CONNECTION_ERROR", status_code=status.HTTP_503_SERVICE_UNAVAILABLE, details=details)

class LLMTimeoutError(BaseAppException):
    """Raised when LLM service times out."""
    def __init__(self, message: str = "LLM generation timed out", details: Optional[Any] = None):
        super().__init__(message=message, code="LLM_TIMEOUT", status_code=status.HTTP_504_GATEWAY_TIMEOUT, details=details)

class BusinessRuleError(BaseAppException):
    """Raised when a business logic rule is violated."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, code="BUSINESS_RULE_ERROR", status_code=status.HTTP_400_BAD_REQUEST, details=details)

class ActionExecutionError(BaseAppException):
    """Raised when an external action (Jira/Slack) fails."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, code="ACTION_EXECUTION_ERROR", status_code=status.HTTP_502_BAD_GATEWAY, details=details)

class IntegrationError(BaseAppException):
    """Raised for general third-party integration failures."""
    def __init__(self, message: str, service_name: str, details: Optional[Any] = None):
        super().__init__(message=message, code=f"INTEGRATION_ERROR_{service_name.upper()}", status_code=status.HTTP_502_BAD_GATEWAY, details=details)
