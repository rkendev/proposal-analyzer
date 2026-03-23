"""
LangGraph orchestrator — implemented in Phase 6.
Handles both analyze and generate modes.
Emits SSE progress events as each agent completes.
"""
import asyncio
import json
import time
from typing import Any

from langgraph.graph import END, StateGraph

from agents.job_intelligence import job_intelligence_agent
from agents.proposal_analyst import proposal_analyst_agent
from agents.rate_intelligence import rate_intelligence_agent
from agents.win_strategy import win_strategy_agent
from exceptions import AgentCallError, OrchestratorError, SchemaValidationError
from schemas.proposal_report import ProposalReport
from schemas.state import ValidatorState

_DEBUG_LOG_PATH = "/root/projects/cursor/proposal-analyzer/.cursor/debug-84c26e.log"

_PROGRESS_EVENTS = (
    {"event": "agent_complete", "agent": "job_intelligence", "progress": 25},
    {"event": "agent_complete", "agent": "rate_intelligence", "progress": 50},
    {"event": "agent_complete", "agent": "proposal_analyst", "progress": 75},
    {"event": "agent_complete", "agent": "win_strategy", "progress": 100},
)


def _debug_log(
    *,
    hypothesis_id: str,
    location: str,
    message: str,
    data: dict[str, Any],
    run_id: str = "pre-fix",
) -> None:
    payload = {
        "sessionId": "84c26e",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    # region agent log
    with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
    # endregion


def _to_validator_state(state: dict[str, Any] | ValidatorState) -> ValidatorState:
    # region agent log
    _debug_log(
        hypothesis_id="H1",
        location="src/orchestrator/graph.py:_to_validator_state",
        message="Validating incoming node state",
        data={
            "state_type": type(state).__name__,
            "keys": sorted(list(state.keys())) if isinstance(state, dict) else [],
            "has_mode": isinstance(state, dict) and ("mode" in state),
            "has_job_posting": isinstance(state, dict) and ("job_posting" in state),
        },
    )
    # endregion
    if isinstance(state, ValidatorState):
        return state
    return ValidatorState.model_validate(state)


def _job_intelligence_node(state: dict[str, Any] | ValidatorState) -> dict:
    # region agent log
    _debug_log(
        hypothesis_id="H2",
        location="src/orchestrator/graph.py:_job_intelligence_node",
        message="Node entry state snapshot",
        data={
            "state_type": type(state).__name__,
            "keys": sorted(list(state.keys())) if isinstance(state, dict) else [],
        },
    )
    # endregion
    return job_intelligence_agent(_to_validator_state(state))


def _rate_intelligence_node(state: dict[str, Any] | ValidatorState) -> dict:
    # region agent log
    _debug_log(
        hypothesis_id="H2",
        location="src/orchestrator/graph.py:_rate_intelligence_node",
        message="Node entry state snapshot",
        data={
            "state_type": type(state).__name__,
            "keys": sorted(list(state.keys())) if isinstance(state, dict) else [],
        },
    )
    # endregion
    return rate_intelligence_agent(_to_validator_state(state))


def _proposal_analyst_node(state: dict[str, Any] | ValidatorState) -> dict:
    # region agent log
    _debug_log(
        hypothesis_id="H2",
        location="src/orchestrator/graph.py:_proposal_analyst_node",
        message="Node entry state snapshot",
        data={
            "state_type": type(state).__name__,
            "keys": sorted(list(state.keys())) if isinstance(state, dict) else [],
        },
    )
    # endregion
    return proposal_analyst_agent(_to_validator_state(state))


def _win_strategy_node(state: dict[str, Any] | ValidatorState) -> dict:
    # region agent log
    _debug_log(
        hypothesis_id="H2",
        location="src/orchestrator/graph.py:_win_strategy_node",
        message="Node entry state snapshot",
        data={
            "state_type": type(state).__name__,
            "keys": sorted(list(state.keys())) if isinstance(state, dict) else [],
        },
    )
    # endregion
    return win_strategy_agent(_to_validator_state(state))


def _build_graph():
    graph_builder = StateGraph(ValidatorState)
    graph_builder.add_node("job_intelligence_node", _job_intelligence_node)
    graph_builder.add_node("rate_intelligence_node", _rate_intelligence_node)
    graph_builder.add_node("proposal_analyst_node", _proposal_analyst_node)
    graph_builder.add_node("win_strategy_node", _win_strategy_node)
    graph_builder.set_entry_point("job_intelligence_node")
    graph_builder.add_edge("job_intelligence_node", "rate_intelligence_node")
    graph_builder.add_edge("rate_intelligence_node", "proposal_analyst_node")
    graph_builder.add_edge("proposal_analyst_node", "win_strategy_node")
    graph_builder.add_edge("win_strategy_node", END)
    return graph_builder.compile()


graph = _build_graph()


def _assemble_report(state: ValidatorState) -> ProposalReport:
    if state.job_id is None:
        raise OrchestratorError("job_id is required to build ProposalReport")
    if state.job_analysis is None:
        raise OrchestratorError("job_analysis missing after orchestration")
    if state.rate_analysis is None:
        raise OrchestratorError("rate_analysis missing after orchestration")
    if state.win_strategy is None:
        raise OrchestratorError("win_strategy missing after orchestration")

    if state.mode == "analyze":
        if state.proposal_critique is None:
            raise OrchestratorError("proposal_critique missing in analyze mode")
        return ProposalReport(
            mode=state.mode,
            job_id=state.job_id,
            job_analysis=state.job_analysis,
            rate_analysis=state.rate_analysis,
            proposal_critique=state.proposal_critique,
            proposal_draft=None,
            win_strategy=state.win_strategy,
            overall_win_readiness_score=state.win_strategy.win_probability_score,
        )

    if state.proposal_draft is None:
        raise OrchestratorError("proposal_draft missing in generate mode")
    return ProposalReport(
        mode=state.mode,
        job_id=state.job_id,
        job_analysis=state.job_analysis,
        rate_analysis=state.rate_analysis,
        proposal_critique=None,
        proposal_draft=state.proposal_draft,
        win_strategy=state.win_strategy,
        overall_win_readiness_score=None,
    )


async def _emit_event(
    event_queue: asyncio.Queue | None, event: dict[str, Any]
) -> None:
    if event_queue is not None:
        await event_queue.put(event)


async def run_orchestrator(
    initial_state: ValidatorState, event_queue: asyncio.Queue | None = None
) -> ProposalReport:
    """
    Run the full LangGraph pipeline and return a final ProposalReport.

    Note: graph.invoke() is synchronous; this async wrapper exists to support
    optional queue-based SSE event emission in later API layers.
    """
    try:
        # region agent log
        _debug_log(
            hypothesis_id="H3",
            location="src/orchestrator/graph.py:run_orchestrator",
            message="Starting graph.invoke",
            data={
                "initial_keys": sorted(list(initial_state.model_dump().keys())),
                "mode": initial_state.mode,
            },
        )
        # endregion
        final_state_dict = graph.invoke(initial_state.model_dump())
        # region agent log
        _debug_log(
            hypothesis_id="H4",
            location="src/orchestrator/graph.py:run_orchestrator",
            message="graph.invoke completed",
            data={
                "final_state_keys": (
                    sorted(list(final_state_dict.keys()))
                    if isinstance(final_state_dict, dict)
                    else []
                ),
                "final_state_type": type(final_state_dict).__name__,
            },
        )
        # endregion
        final_state = ValidatorState.model_validate(final_state_dict)
        report = _assemble_report(final_state)

        for event in _PROGRESS_EVENTS:
            await _emit_event(event_queue, event)
        await _emit_event(
            event_queue,
            {"event": "complete", "data": report.model_dump_json()},
        )
        return report
    except (AgentCallError, SchemaValidationError) as e:
        await _emit_event(event_queue, {"event": "error", "message": str(e)})
        raise OrchestratorError(str(e)) from e
    except OrchestratorError as e:
        await _emit_event(event_queue, {"event": "error", "message": str(e)})
        raise
    except Exception as e:
        await _emit_event(event_queue, {"event": "error", "message": str(e)})
        raise OrchestratorError(str(e)) from e
