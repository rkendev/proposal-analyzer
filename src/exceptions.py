"""
Custom exception hierarchy for Freelance Proposal Analyzer.

These exceptions are created in Phase 0 and referenced throughout.
FastAPI layer catches them and maps to HTTP status codes:
  AgentCallError      → 422
  SchemaValidationError → 422
  All others          → 500
"""


class ProposalAnalyzerError(Exception):
    """Base exception for all project errors."""
    pass


class AgentCallError(ProposalAnalyzerError):
    """Raised when an LLM agent call fails.

    Examples:
        - LiteLLM API error
        - Model timeout
        - Rate limit hit
    """
    def __init__(self, agent_name: str, message: str):
        self.agent_name = agent_name
        super().__init__(f"Agent [{agent_name}] failed: {message}")


class SchemaValidationError(ProposalAnalyzerError):
    """Raised when agent output fails Pydantic v2 validation.

    Examples:
        - LLM returned JSON with missing required fields
        - Score field out of expected range
        - Wrong enum value
    """
    def __init__(self, agent_name: str, message: str):
        self.agent_name = agent_name
        super().__init__(
            f"Schema validation failed for [{agent_name}]: {message}"
        )


class OrchestratorError(ProposalAnalyzerError):
    """Raised when the LangGraph orchestrator encounters an error
    that is not attributable to a specific agent."""
    pass
