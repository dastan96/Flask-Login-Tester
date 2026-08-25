import json
import os

from openai import OpenAI, OpenAIError

from services import ai_analysis_contract, analysis_context_service


DEFAULT_MODEL = "gpt-5.6-terra"
SCHEMA_NAME = "qa_change_impact_analysis"


class OpenAIAnalysisServiceError(Exception):
    def __init__(self, message, *, code):
        super().__init__(message)
        self.code = code


def _create_client():
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise OpenAIAnalysisServiceError(
            "OpenAI API key is not configured.",
            code="missing_api_key",
        )
    return OpenAI()


def _resolve_model(model):
    return model or os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL


def analyze_context(analysis_context, *, client=None, model=None):
    openai_client = client if client is not None else _create_client()
    model_input = ai_analysis_contract.build_ai_input(analysis_context)

    try:
        response = openai_client.responses.create(
            model=_resolve_model(model),
            instructions=ai_analysis_contract.STABLE_ANALYSIS_INSTRUCTIONS,
            input=model_input,
            text={
                "format": {
                    "type": "json_schema",
                    "name": SCHEMA_NAME,
                    "schema": ai_analysis_contract.AI_ANALYSIS_OUTPUT_SCHEMA,
                    "strict": True,
                }
            },
            store=False,
        )
    except OpenAIError as error:
        raise OpenAIAnalysisServiceError(
            "OpenAI analysis request failed.",
            code="openai_request_failed",
        ) from error

    output_text = getattr(response, "output_text", None)
    if not isinstance(output_text, str) or not output_text.strip():
        raise OpenAIAnalysisServiceError(
            "OpenAI returned no analysis output.",
            code="missing_model_output",
        )

    try:
        analysis = json.loads(output_text)
    except json.JSONDecodeError as error:
        raise OpenAIAnalysisServiceError(
            "OpenAI returned malformed analysis JSON.",
            code="invalid_json_output",
        ) from error

    if not isinstance(analysis, dict):
        raise OpenAIAnalysisServiceError(
            "OpenAI returned an invalid analysis structure.",
            code="invalid_model_output",
        )
    return analysis


def analyze_pull_request(pr_number, *, client=None, model=None):
    analysis_context = analysis_context_service.build_analysis_context(pr_number)
    return analyze_context(analysis_context, client=client, model=model)
