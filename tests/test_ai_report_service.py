import json
from datetime import datetime

import pytest

from services import ai_report_service
from services.openai_analysis_service import OpenAIAnalysisServiceError


GENERATED_AT = "2026-08-24T21:00:00Z"


def sample_analysis_context(pr_number=42):
    return {
        "pull_request": {
            "number": pr_number,
            "title": "Add persistent AI QA reports",
            "description": "Adds report persistence.",
            "state": "closed",
            "merged_at": "2026-08-24T20:30:00Z",
            "source_branch": "feature/ai-reports",
            "target_branch": "main",
            "commit_sha": "abc123",
            "github_url": f"https://github.com/dastan96/Flask-Login-Tester/pull/{pr_number}",
        },
        "change_summary": {
            "files_changed": 3,
            "additions": 20,
            "deletions": 4,
            "total_changes": 24,
        },
        "changed_files": [],
        "qa_context": {"suites": [], "tests": []},
    }


def sample_analysis(risk_level="medium"):
    return {
        "prompt_version": "1.0",
        "risk_level": risk_level,
        "change_summary": "The Pull Request adds local AI report persistence.",
        "risk_rationale": "Filesystem publication requires careful failure handling.",
        "affected_areas": [],
        "relevant_existing_tests": [],
        "coverage_gaps": [],
        "recommended_tests": [],
        "qa_notes": [],
        "analysis_limitations": [],
    }


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def install_generation_mocks(monkeypatch, context, analysis):
    calls = {"context": [], "analysis": [], "model": []}

    def build_analysis_context(pr_number):
        calls["context"].append(pr_number)
        return context

    def resolve_model(model=None):
        calls["model"].append(model)
        return model or "resolved-test-model"

    def analyze_context(received_context, *, client=None, model=None):
        calls["analysis"].append(
            {
                "context": received_context,
                "client": client,
                "model": model,
            }
        )
        return analysis

    monkeypatch.setattr(
        ai_report_service.analysis_context_service,
        "build_analysis_context",
        build_analysis_context,
    )
    monkeypatch.setattr(
        ai_report_service.openai_analysis_service,
        "resolve_model",
        resolve_model,
    )
    monkeypatch.setattr(
        ai_report_service.openai_analysis_service,
        "analyze_context",
        analyze_context,
    )
    monkeypatch.setattr(ai_report_service, "utc_now_iso", lambda: GENERATED_AT)
    return calls


def test_generate_report_reuses_context_and_writes_public_artifacts(tmp_path, monkeypatch):
    context = sample_analysis_context()
    analysis = sample_analysis()
    client = object()
    calls = install_generation_mocks(monkeypatch, context, analysis)
    monkeypatch.setenv("OPENAI_API_KEY", "api-key-secret-sentinel")
    monkeypatch.setenv("UNRELATED_SECRET", "environment-secret-sentinel")
    output_dir = tmp_path / "public" / "ai"

    result = ai_report_service.generate_ai_report(
        42,
        output_dir=output_dir,
        client=client,
    )

    expected_report = {
        "report_version": "1.0",
        "prompt_version": "1.0",
        "generated_at": GENERATED_AT,
        "model": "resolved-test-model",
        "source": {
            "pr_number": 42,
            "pr_title": "Add persistent AI QA reports",
            "github_url": "https://github.com/dastan96/Flask-Login-Tester/pull/42",
            "merged_at": "2026-08-24T20:30:00Z",
            "commit_sha": "abc123",
        },
        "change_summary": context["change_summary"],
        "analysis": analysis,
    }
    assert result.generated is True
    assert result.skipped is False
    assert result.model == "resolved-test-model"
    assert result.report == expected_report
    assert result.report_path == output_dir / "reports" / "pr-42.json"
    assert calls["context"] == [42]
    assert calls["model"] == [None]
    assert calls["analysis"] == [
        {
            "context": context,
            "client": client,
            "model": "resolved-test-model",
        }
    ]

    report = read_json(result.report_path)
    latest = read_json(output_dir / "latest.json")
    index = read_json(output_dir / "index.json")
    assert report == expected_report
    assert latest == expected_report
    assert index == {
        "report_version": "1.0",
        "reports": [
            {
                "pr_number": 42,
                "title": "Add persistent AI QA reports",
                "risk_level": "medium",
                "generated_at": GENERATED_AT,
                "model": "resolved-test-model",
                "prompt_version": "1.0",
                "report_path": "reports/pr-42.json",
            }
        ],
    }
    assert "analysis" not in index["reports"][0]
    assert datetime.fromisoformat(report["generated_at"].replace("Z", "+00:00")).tzinfo is not None

    public_output = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [result.report_path, output_dir / "latest.json", output_dir / "index.json"]
    )
    assert "api-key-secret-sentinel" not in public_output
    assert "environment-secret-sentinel" not in public_output


def report_for_index(pr_number, generated_at, risk_level="low"):
    context = sample_analysis_context(pr_number)
    context["pull_request"]["title"] = f"Pull Request {pr_number}"
    return {
        "report_version": "1.0",
        "prompt_version": "1.0",
        "generated_at": generated_at,
        "model": "test-model",
        "source": {
            "pr_number": pr_number,
            "pr_title": context["pull_request"]["title"],
            "github_url": context["pull_request"]["github_url"],
            "merged_at": context["pull_request"]["merged_at"],
            "commit_sha": context["pull_request"]["commit_sha"],
        },
        "change_summary": context["change_summary"],
        "analysis": sample_analysis(risk_level),
    }


def test_rebuild_index_is_deterministic_and_ignores_malformed_reports(tmp_path):
    output_dir = tmp_path / "public" / "ai"
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "pr-2.json").write_text(
        json.dumps(report_for_index(2, "2026-08-23T10:00:00Z")),
        encoding="utf-8",
    )
    (reports_dir / "pr-3.json").write_text(
        json.dumps(report_for_index(3, "2026-08-24T10:00:00Z", "high")),
        encoding="utf-8",
    )
    (reports_dir / "pr-4.json").write_text(
        json.dumps(report_for_index(4, "2026-08-24T10:00:00Z", "medium")),
        encoding="utf-8",
    )
    (reports_dir / "pr-broken.json").write_text("not JSON", encoding="utf-8")
    (reports_dir / "pr-invalid.json").write_text(json.dumps({"unexpected": True}), encoding="utf-8")

    first = ai_report_service.rebuild_report_index(output_dir)
    second = ai_report_service.rebuild_report_index(output_dir)

    assert first == second
    assert [entry["pr_number"] for entry in first["reports"]] == [4, 3, 2]
    assert all("analysis" not in entry for entry in first["reports"])
    assert read_json(output_dir / "index.json") == first


def test_existing_report_is_skipped_without_context_or_ai_calls(tmp_path, monkeypatch):
    output_dir = tmp_path / "public" / "ai"
    report_path = output_dir / "reports" / "pr-42.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text('{"existing": true}\n', encoding="utf-8")

    def unexpected_call(*_args, **_kwargs):
        raise AssertionError("generation dependency should not be called")

    monkeypatch.setattr(
        ai_report_service.analysis_context_service,
        "build_analysis_context",
        unexpected_call,
    )
    monkeypatch.setattr(
        ai_report_service.openai_analysis_service,
        "analyze_context",
        unexpected_call,
    )

    result = ai_report_service.generate_ai_report(42, output_dir=output_dir)

    assert result.generated is False
    assert result.skipped is True
    assert result.report_path == report_path
    assert report_path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_force_regenerates_existing_report(tmp_path, monkeypatch):
    output_dir = tmp_path / "public" / "ai"
    report_path = output_dir / "reports" / "pr-42.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text('{"old": true}\n', encoding="utf-8")
    calls = install_generation_mocks(
        monkeypatch,
        sample_analysis_context(),
        sample_analysis("high"),
    )

    result = ai_report_service.generate_ai_report(
        42,
        output_dir=output_dir,
        force=True,
        client=object(),
        model="forced-model",
    )

    assert result.generated is True
    assert calls["context"] == [42]
    assert len(calls["analysis"]) == 1
    assert read_json(report_path)["analysis"]["risk_level"] == "high"
    assert read_json(report_path)["model"] == "forced-model"


def test_failed_analysis_does_not_publish_report_files(tmp_path, monkeypatch):
    output_dir = tmp_path / "public" / "ai"
    context = sample_analysis_context()
    monkeypatch.setattr(
        ai_report_service.analysis_context_service,
        "build_analysis_context",
        lambda _pr_number: context,
    )
    monkeypatch.setattr(
        ai_report_service.openai_analysis_service,
        "resolve_model",
        lambda _model=None: "test-model",
    )

    def fail(*_args, **_kwargs):
        raise OpenAIAnalysisServiceError(
            "OpenAI analysis request failed.",
            code="openai_request_failed",
        )

    monkeypatch.setattr(
        ai_report_service.openai_analysis_service,
        "analyze_context",
        fail,
    )

    with pytest.raises(OpenAIAnalysisServiceError):
        ai_report_service.generate_ai_report(42, output_dir=output_dir, client=object())

    assert not (output_dir / "reports" / "pr-42.json").exists()
    assert not (output_dir / "latest.json").exists()
    assert not (output_dir / "index.json").exists()
