import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from services import ai_analysis_contract, analysis_context_service, openai_analysis_service


REPORT_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AI_REPORT_DIR = PROJECT_ROOT / "public" / "ai"


@dataclass(frozen=True)
class AIReportGenerationResult:
    generated: bool
    pr_number: int
    report_path: Path
    model: str | None = None
    report: dict | None = None

    @property
    def skipped(self):
        return not self.generated


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _atomic_write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(data, output, indent=2, sort_keys=True, ensure_ascii=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _load_report(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _index_entry(report, report_path):
    if not isinstance(report, dict):
        return None
    source = report.get("source")
    analysis = report.get("analysis")
    if not isinstance(source, dict) or not isinstance(analysis, dict):
        return None

    values = {
        "pr_number": source.get("pr_number"),
        "title": source.get("pr_title"),
        "risk_level": analysis.get("risk_level"),
        "generated_at": report.get("generated_at"),
        "model": report.get("model"),
        "prompt_version": report.get("prompt_version"),
    }
    if not isinstance(values["pr_number"], int) or isinstance(values["pr_number"], bool):
        return None
    if not all(isinstance(values[field], str) for field in values if field != "pr_number"):
        return None

    return {
        **values,
        "report_path": f"reports/{report_path.name}",
    }


def rebuild_report_index(output_dir=DEFAULT_AI_REPORT_DIR):
    output_path = Path(output_dir)
    reports_dir = output_path / "reports"
    entries = []

    if reports_dir.exists():
        for report_path in sorted(reports_dir.glob("pr-*.json")):
            entry = _index_entry(_load_report(report_path), report_path)
            if entry is not None:
                entries.append(entry)

    entries.sort(
        key=lambda entry: (entry["generated_at"], entry["pr_number"]),
        reverse=True,
    )
    index = {
        "report_version": REPORT_VERSION,
        "reports": entries,
    }
    _atomic_write_json(output_path / "index.json", index)
    return index


def _build_report(analysis_context, analysis, *, model, generated_at):
    pull_request = analysis_context["pull_request"]
    return {
        "report_version": REPORT_VERSION,
        "prompt_version": ai_analysis_contract.PROMPT_VERSION,
        "generated_at": generated_at,
        "model": model,
        "source": {
            "pr_number": pull_request["number"],
            "pr_title": pull_request["title"],
            "github_url": pull_request["github_url"],
            "merged_at": pull_request["merged_at"],
            "commit_sha": pull_request["commit_sha"],
        },
        "change_summary": analysis_context["change_summary"],
        "analysis": analysis,
    }


def generate_ai_report(
    pr_number,
    *,
    output_dir=DEFAULT_AI_REPORT_DIR,
    force=False,
    client=None,
    model=None,
):
    if not isinstance(pr_number, int) or isinstance(pr_number, bool) or pr_number <= 0:
        raise ValueError("pr_number must be a positive integer")

    output_path = Path(output_dir)
    report_path = output_path / "reports" / f"pr-{pr_number}.json"
    if report_path.exists() and not force:
        return AIReportGenerationResult(
            generated=False,
            pr_number=pr_number,
            report_path=report_path,
        )

    analysis_context = analysis_context_service.build_analysis_context(pr_number)
    selected_model = openai_analysis_service.resolve_model(model)
    analysis = openai_analysis_service.analyze_context(
        analysis_context,
        client=client,
        model=selected_model,
    )
    report = _build_report(
        analysis_context,
        analysis,
        model=selected_model,
        generated_at=utc_now_iso(),
    )

    _atomic_write_json(report_path, report)
    _atomic_write_json(output_path / "latest.json", report)
    rebuild_report_index(output_path)

    return AIReportGenerationResult(
        generated=True,
        pr_number=pr_number,
        report_path=report_path,
        model=selected_model,
        report=report,
    )
