import json
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app, jobs


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from api.main import limiter

    reset_fn = getattr(limiter, "reset", None)
    if callable(reset_fn):
        reset_fn()
    else:
        limiter._storage.reset()
    yield
    if callable(reset_fn):
        reset_fn()
    else:
        limiter._storage.reset()


def _mock_run_orchestrator_factory(sample_proposal_report_analyze):
    async def _mock_run_orchestrator(initial_state, event_queue=None):
        report = sample_proposal_report_analyze.model_copy(
            update={"mode": initial_state.mode, "job_id": initial_state.job_id}
        )
        if event_queue is not None:
            event_queue.put_nowait(
                {"event": "agent_complete", "agent": "job_intelligence", "progress": 25}
            )
            event_queue.put_nowait(
                {"event": "agent_complete", "agent": "rate_intelligence", "progress": 50}
            )
            event_queue.put_nowait(
                {"event": "agent_complete", "agent": "proposal_analyst", "progress": 75}
            )
            event_queue.put_nowait(
                {"event": "agent_complete", "agent": "win_strategy", "progress": 100}
            )
            event_queue.put_nowait(
                {"event": "complete", "data": report.model_dump_json()}
            )
        return report

    return _mock_run_orchestrator


def test_post_analyze_returns_job_id_within_200ms(
    sample_analyze_request, sample_proposal_report_analyze
):
    jobs.clear()
    mock_runner = AsyncMock(
        side_effect=_mock_run_orchestrator_factory(sample_proposal_report_analyze)
    )
    with patch("api.main.run_orchestrator", mock_runner):
        client = TestClient(app)
        start = time.perf_counter()
        response = client.post("/analyze", json=sample_analyze_request)
        elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    assert "job_id" in response.json()
    assert elapsed_ms < 200


def test_post_generate_returns_job_id_within_200ms(
    sample_generate_request, sample_proposal_report_analyze
):
    jobs.clear()
    mock_runner = AsyncMock(
        side_effect=_mock_run_orchestrator_factory(sample_proposal_report_analyze)
    )
    with patch("api.main.run_orchestrator", mock_runner):
        client = TestClient(app)
        start = time.perf_counter()
        response = client.post("/generate", json=sample_generate_request)
        elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    assert "job_id" in response.json()
    assert elapsed_ms < 200


def test_get_health_returns_expected_body():
    jobs.clear()
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


def test_stream_endpoint_emits_sse_and_complete_event(
    sample_analyze_request, sample_proposal_report_analyze
):
    jobs.clear()
    mock_runner = AsyncMock(
        side_effect=_mock_run_orchestrator_factory(sample_proposal_report_analyze)
    )
    with patch("api.main.run_orchestrator", mock_runner):
        client = TestClient(app)
        create_response = client.post("/analyze", json=sample_analyze_request)
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        lines: list[str] = []
        with client.stream("GET", f"/stream/{job_id}") as response:
            assert response.status_code == 200
            for line in response.iter_lines():
                if line:
                    lines.append(line)
                if line.startswith("data: ") and '"event": "complete"' in line:
                    break

    data_lines = [line for line in lines if line.startswith("data: ")]
    assert len(data_lines) >= 5

    final_event = json.loads(data_lines[-1].replace("data: ", "", 1))
    assert final_event["event"] == "complete"
    final_report = json.loads(final_event["data"])
    assert final_report["job_id"] == job_id
    assert final_report["mode"] == "analyze"


def test_stream_unknown_job_returns_404():
    jobs.clear()
    client = TestClient(app)
    response = client.get("/stream/does-not-exist")
    assert response.status_code == 404


def test_rate_limit_analyze_returns_429_after_ten_requests(
    sample_analyze_request, sample_proposal_report_analyze
):
    jobs.clear()
    mock_runner = AsyncMock(
        side_effect=_mock_run_orchestrator_factory(sample_proposal_report_analyze)
    )
    with patch("api.main.run_orchestrator", mock_runner):
        client = TestClient(app)
        responses = [
            client.post("/analyze", json=sample_analyze_request) for _ in range(10)
        ]
        assert all(response.status_code == 200 for response in responses)
        limited = client.post("/analyze", json=sample_analyze_request)
    assert limited.status_code == 429


def test_rate_limit_generate_returns_429_after_ten_requests(
    sample_generate_request, sample_proposal_report_analyze
):
    jobs.clear()
    mock_runner = AsyncMock(
        side_effect=_mock_run_orchestrator_factory(sample_proposal_report_analyze)
    )
    with patch("api.main.run_orchestrator", mock_runner):
        client = TestClient(app)
        responses = [
            client.post("/generate", json=sample_generate_request) for _ in range(10)
        ]
        assert all(response.status_code == 200 for response in responses)
        limited = client.post("/generate", json=sample_generate_request)
    assert limited.status_code == 429


def test_cors_headers_present(sample_analyze_request, sample_proposal_report_analyze):
    jobs.clear()
    mock_runner = AsyncMock(
        side_effect=_mock_run_orchestrator_factory(sample_proposal_report_analyze)
    )
    with patch("api.main.run_orchestrator", mock_runner):
        client = TestClient(app)
        response = client.post(
            "/analyze",
            json=sample_analyze_request,
            headers={"Origin": "http://localhost:3000"},
        )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_post_analyze_short_job_posting_returns_422(sample_analyze_request):
    jobs.clear()
    client = TestClient(app)
    invalid_request = {
        "job_posting": "too short",
        "proposal_draft": sample_analyze_request["proposal_draft"],
        "mode": "analyze",
    }
    response = client.post("/analyze", json=invalid_request)
    assert response.status_code == 422
