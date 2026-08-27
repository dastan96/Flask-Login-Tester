import json

import pytest
from openai import OpenAIError

from services import openai_analysis_service
from services.github_pr_service import GitHubPRServiceError
from services.openai_analysis_service import OpenAIAnalysisServiceError


def sample_analysis():
    return {
        "prompt_version": "1.0",
        "risk_level": "medium",
        "change_summary": "The Pull Request changes login validation behavior.",
        "risk_rationale": "Authentication paths are user-facing and security-sensitive.",
        "affected_areas": [
            {
                "area": "Login authentication",
                "evidence": "The login handler patch changes credential validation.",
            }
        ],
        "relevant_existing_tests": [
            {
                "test_id": "01.03",
                "title": "Login wrong password",
                "reason": "It exercises the modified invalid-credential path.",
            }
        ],
        "coverage_gaps": [],
        "recommended_tests": [],
        "qa_notes": ["Review both JSON and browser-form behavior."],
        "analysis_limitations": [],
    }


class MockResponse:
    def __init__(self, output_text):
        self.output_text = output_text


class MockResponses:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class MockClient:
    def __init__(self, response=None, error=None):
        self.responses = MockResponses(response=response, error=error)


def test_analyze_pull_request_builds_context_and_sends_structured_request(monkeypatch):
    context = {"pull_request": {"number": 42}}
    model_input = "prepared deterministic context"
    expected_analysis = sample_analysis()
    client = MockClient(MockResponse(json.dumps(expected_analysis)))
    context_calls = []
    input_calls = []

    def build_analysis_context(pr_number):
        context_calls.append(pr_number)
        return context

    def build_ai_input(analysis_context):
        input_calls.append(analysis_context)
        return model_input

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        openai_analysis_service.analysis_context_service,
        "build_analysis_context",
        build_analysis_context,
    )
    monkeypatch.setattr(
        openai_analysis_service.ai_analysis_contract,
        "build_ai_input",
        build_ai_input,
    )

    result = openai_analysis_service.analyze_pull_request(
        42,
        client=client,
        model="test-analysis-model",
    )

    assert result == expected_analysis
    assert context_calls == [42]
    assert input_calls == [context]
    assert len(client.responses.calls) == 1
    request = client.responses.calls[0]
    assert request == {
        "model": "test-analysis-model",
        "instructions": openai_analysis_service.ai_analysis_contract.STABLE_ANALYSIS_INSTRUCTIONS,
        "input": model_input,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "qa_change_impact_analysis",
                "schema": openai_analysis_service.ai_analysis_contract.AI_ANALYSIS_OUTPUT_SCHEMA,
                "strict": True,
            }
        },
        "store": False,
    }


def test_openai_model_environment_override(monkeypatch):
    client = MockClient(MockResponse(json.dumps(sample_analysis())))
    monkeypatch.setenv("OPENAI_MODEL", "environment-model")

    openai_analysis_service.analyze_context({}, client=client)

    assert client.responses.calls[0]["model"] == "environment-model"


def test_default_model_is_used_when_no_override_exists(monkeypatch):
    client = MockClient(MockResponse(json.dumps(sample_analysis())))
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    openai_analysis_service.analyze_context({}, client=client)

    assert client.responses.calls[0]["model"] == openai_analysis_service.DEFAULT_MODEL
    assert openai_analysis_service.DEFAULT_MODEL == "gpt-5.6-terra"


@pytest.mark.parametrize("output_text", [None, "", "   "])
def test_missing_or_empty_model_output_raises_service_error(output_text):
    client = MockClient(MockResponse(output_text))

    with pytest.raises(OpenAIAnalysisServiceError) as error:
        openai_analysis_service.analyze_context({}, client=client)

    assert error.value.code == "missing_model_output"
    assert str(error.value) == "OpenAI returned no analysis output."


def test_malformed_json_raises_service_error():
    client = MockClient(MockResponse("not valid JSON"))

    with pytest.raises(OpenAIAnalysisServiceError) as error:
        openai_analysis_service.analyze_context({}, client=client)

    assert error.value.code == "invalid_json_output"
    assert str(error.value) == "OpenAI returned malformed analysis JSON."


def test_non_object_json_raises_service_error():
    client = MockClient(MockResponse("[]"))

    with pytest.raises(OpenAIAnalysisServiceError) as error:
        openai_analysis_service.analyze_context({}, client=client)

    assert error.value.code == "invalid_model_output"


def test_openai_sdk_failure_raises_service_error():
    client = MockClient(error=OpenAIError("mock request failure"))

    with pytest.raises(OpenAIAnalysisServiceError) as error:
        openai_analysis_service.analyze_context({}, client=client)

    assert error.value.code == "openai_request_failed"
    assert str(error.value) == "OpenAI analysis request failed."


def test_missing_api_key_raises_friendly_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(OpenAIAnalysisServiceError) as error:
        openai_analysis_service.analyze_context({})

    assert error.value.code == "missing_api_key"
    assert str(error.value) == "OpenAI API key is not configured."


def test_upstream_context_failure_is_not_reclassified(monkeypatch):
    failure = GitHubPRServiceError(
        "GitHub API request failed.",
        code="github_http_error",
        status_code=403,
    )
    client = MockClient(MockResponse(json.dumps(sample_analysis())))

    def fail(_pr_number):
        raise failure

    monkeypatch.setattr(
        openai_analysis_service.analysis_context_service,
        "build_analysis_context",
        fail,
    )

    with pytest.raises(GitHubPRServiceError) as error:
        openai_analysis_service.analyze_pull_request(42, client=client)

    assert error.value is failure
    assert client.responses.calls == []
