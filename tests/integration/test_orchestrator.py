"""Integration tests for LangGraph orchestrator with mocked agents."""

import asyncio
from unittest.mock import patch

import pytest

from exceptions import AgentCallError, OrchestratorError, SchemaValidationError
from orchestrator.graph import run_orchestrator
from schemas.proposal_report import ProposalReport
from schemas.state import ValidatorState


def _initial_state_analyze(sample_analyze_request) -> ValidatorState:
    return ValidatorState(
        mode="analyze",
        job_posting=sample_analyze_request["job_posting"],
        proposal_draft_text=sample_analyze_request["proposal_draft"],
        job_id="00000000-0000-4000-8000-000000000010",
    )


def _initial_state_generate(sample_generate_request) -> ValidatorState:
    return ValidatorState(
        mode="generate",
        job_posting=sample_generate_request["job_posting"],
        proposal_draft_text=None,
        job_id="00000000-0000-4000-8000-000000000011",
    )


@pytest.mark.asyncio
@patch("orchestrator.graph.win_strategy_agent")
@patch("orchestrator.graph.proposal_analyst_agent")
@patch("orchestrator.graph.rate_intelligence_agent")
@patch("orchestrator.graph.job_intelligence_agent")
async def test_analyze_mode_full_pipeline_and_sse_events(
    mock_job,
    mock_rate,
    mock_proposal,
    mock_win,
    sample_analyze_request,
    sample_job_analysis,
    sample_rate_analysis,
    sample_proposal_critique,
    sample_win_strategy,
):
    mock_job.return_value = {"job_analysis": sample_job_analysis}
    mock_rate.return_value = {"rate_analysis": sample_rate_analysis}
    mock_proposal.return_value = {"proposal_critique": sample_proposal_critique}
    mock_win.return_value = {"win_strategy": sample_win_strategy}
    queue: asyncio.Queue = asyncio.Queue()

    report = await run_orchestrator(
        _initial_state_analyze(sample_analyze_request), event_queue=queue
    )

    assert isinstance(report, ProposalReport)
    assert report.mode == "analyze"
    assert report.proposal_critique is not None
    assert report.proposal_draft is None
    assert (
        report.overall_win_readiness_score
        == report.win_strategy.win_probability_score
    )

    events = [queue.get_nowait() for _ in range(5)]
    assert events[:4] == [
        {"event": "agent_complete", "agent": "job_intelligence", "progress": 25},
        {"event": "agent_complete", "agent": "rate_intelligence", "progress": 50},
        {"event": "agent_complete", "agent": "proposal_analyst", "progress": 75},
        {"event": "agent_complete", "agent": "win_strategy", "progress": 100},
    ]
    assert events[4]["event"] == "complete"
    complete_report = ProposalReport.model_validate_json(events[4]["data"])
    assert complete_report.mode == "analyze"
    assert complete_report.proposal_critique is not None
    assert complete_report.proposal_draft is None


@pytest.mark.asyncio
@patch("orchestrator.graph.win_strategy_agent")
@patch("orchestrator.graph.proposal_analyst_agent")
@patch("orchestrator.graph.rate_intelligence_agent")
@patch("orchestrator.graph.job_intelligence_agent")
async def test_generate_mode_full_pipeline_assembles_report(
    mock_job,
    mock_rate,
    mock_proposal,
    mock_win,
    sample_generate_request,
    sample_job_analysis,
    sample_rate_analysis,
    sample_proposal_draft,
    sample_win_strategy,
):
    mock_job.return_value = {"job_analysis": sample_job_analysis}
    mock_rate.return_value = {"rate_analysis": sample_rate_analysis}
    mock_proposal.return_value = {"proposal_draft": sample_proposal_draft}
    mock_win.return_value = {"win_strategy": sample_win_strategy}
    queue: asyncio.Queue = asyncio.Queue()

    report = await run_orchestrator(
        _initial_state_generate(sample_generate_request), event_queue=queue
    )

    assert isinstance(report, ProposalReport)
    assert report.mode == "generate"
    assert report.proposal_critique is None
    assert report.proposal_draft is not None
    assert report.overall_win_readiness_score is None

    complete_event = [queue.get_nowait() for _ in range(5)][4]
    assert complete_event["event"] == "complete"
    parsed = ProposalReport.model_validate_json(complete_event["data"])
    assert parsed.mode == "generate"
    assert parsed.proposal_critique is None
    assert parsed.proposal_draft is not None


@pytest.mark.asyncio
@patch("orchestrator.graph.win_strategy_agent")
@patch("orchestrator.graph.proposal_analyst_agent")
@patch("orchestrator.graph.rate_intelligence_agent")
@patch("orchestrator.graph.job_intelligence_agent")
async def test_agent_sequence_called_in_correct_order(
    mock_job,
    mock_rate,
    mock_proposal,
    mock_win,
    sample_analyze_request,
    sample_job_analysis,
    sample_rate_analysis,
    sample_proposal_critique,
    sample_win_strategy,
):
    call_order: list[str] = []

    def _job(state):
        call_order.append("job_intelligence")
        return {"job_analysis": sample_job_analysis}

    def _rate(state):
        call_order.append("rate_intelligence")
        return {"rate_analysis": sample_rate_analysis}

    def _proposal(state):
        call_order.append("proposal_analyst")
        return {"proposal_critique": sample_proposal_critique}

    def _win(state):
        call_order.append("win_strategy")
        return {"win_strategy": sample_win_strategy}

    mock_job.side_effect = _job
    mock_rate.side_effect = _rate
    mock_proposal.side_effect = _proposal
    mock_win.side_effect = _win

    await run_orchestrator(_initial_state_analyze(sample_analyze_request))

    assert call_order == [
        "job_intelligence",
        "rate_intelligence",
        "proposal_analyst",
        "win_strategy",
    ]


@pytest.mark.asyncio
@patch("orchestrator.graph.job_intelligence_agent")
async def test_orchestrator_error_when_agent_call_error(mock_job, sample_analyze_request):
    mock_job.side_effect = AgentCallError("job_intelligence", "llm timeout")
    queue: asyncio.Queue = asyncio.Queue()

    with pytest.raises(OrchestratorError) as exc_info:
        await run_orchestrator(
            _initial_state_analyze(sample_analyze_request), event_queue=queue
        )

    assert "llm timeout" in str(exc_info.value)
    error_event = queue.get_nowait()
    assert error_event["event"] == "error"
    assert "llm timeout" in error_event["message"]


@pytest.mark.asyncio
@patch("orchestrator.graph.job_intelligence_agent")
async def test_orchestrator_error_when_schema_validation_error(
    mock_job, sample_analyze_request
):
    mock_job.side_effect = SchemaValidationError("job_intelligence", "invalid enum")
    queue: asyncio.Queue = asyncio.Queue()

    with pytest.raises(OrchestratorError) as exc_info:
        await run_orchestrator(
            _initial_state_analyze(sample_analyze_request), event_queue=queue
        )

    assert "invalid enum" in str(exc_info.value)
    error_event = queue.get_nowait()
    assert error_event["event"] == "error"
    assert "invalid enum" in error_event["message"]
