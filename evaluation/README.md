# AI Analysis Evaluation

This directory contains a small, deterministic evaluation harness for the AI-assisted QA change-impact analyst. It measures grounding, risk calibration, test relevance, recommendation restraint, limitations, and resistance to unsupported or injected claims without using another model as a grader.

## Controlled Scenarios

- `login-behavior-change` checks authentication impact, existing login-test grounding, and focused regression recommendations.
- `documentation-only` checks low-risk calibration and restraint for a README-only change.
- `prompt-injection-incomplete-evidence` checks prompt-injection resistance and explicit uncertainty when patch evidence is absent.

Each case supplies a controlled AI-3 analysis context and deterministic criteria. Structural and integrity properties are checked in Python; nuanced prose quality remains a human-review concern.

## Running Evaluations

List cases without contacting OpenAI:

```bash
python scripts/run_ai_evaluation.py --list
```

Run an explicit live evaluation:

```bash
python scripts/run_ai_evaluation.py --live
python scripts/run_ai_evaluation.py --live --case login-behavior-change
```

Live mode requires `OPENAI_API_KEY` and uses the existing model-resolution logic. Normal pytest execution uses fixture analyses and never invokes OpenAI.

## First Live Evaluation

The first live evaluation with `gpt-5.6-terra` produced `32/35` passing checks. Manual review classified all three failures as evaluation-oracle brittleness rather than prompt or model failures: one defensible UI-test reference in the documentation case and two checks tied to incidental wording.

The criteria were calibrated to preserve structural grounding and safety checks while reducing dependence on exact prose. No second live run was performed solely to manufacture a perfect score, and no post-calibration live score is claimed.
