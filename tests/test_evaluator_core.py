"""Unit tests for the CodeBroker report evaluation functions.

This module tests source code loading, report parsing, JAX metric computation,
and Polars summary generation for the CodeBroker evaluation pipeline.
"""

import os
import tempfile
import pytest
import jax.numpy as jnp
import polars as pl
from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    """Evaluation score and feedback for an individual quality dimension."""

    score: float = Field(ge=0.0, le=100.0, description="Score from 0 to 100")
    weight: float = Field(ge=0.0, le=1.0, description="Weight between 0 and 1")
    rationale: str = Field(description="Explanation of score")
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class CodeBrokerQualityReport(BaseModel):
    """Comprehensive evaluation of a CodeBroker report."""

    faithfulness: DimensionScore
    completeness: DimensionScore
    actionability: DimensionScore
    scoring_calibration: DimensionScore
    structure_adherence: DimensionScore
    code_broker_scores_critique: str = ""
    identified_hallucinations: list[str] = Field(default_factory=list)
    missed_code_issues: list[str] = Field(default_factory=list)
    executive_summary: str
    actionable_recommendations_for_report: list[str] = Field(default_factory=list)


def load_source_code(target_path: str) -> dict[str, str]:
    """Loads source code from a file or directory.

    Args:
        target_path: Path to a file or directory.

    Returns:
        Dictionary mapping file paths to code contents.
    """
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Path does not exist: {target_path}")

    results = {}
    if os.path.isfile(target_path):
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            results[os.path.basename(target_path)] = f.read()
        return results

    skip_dirs = {".git", "__pycache__", ".venv", ".pytest_cache", ".agents"}
    skip_exts = {".pyc", ".png", ".jpg", ".jpeg", ".pdf", ".zip", ".tar", ".gz", ".eps"}

    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in skip_exts:
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, target_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
                    results[rel_path] = fp.read()
            except Exception:
                continue
    return results


def load_code_broker_report(report_path_or_content: str) -> str:
    """Parses a CodeBroker report from a markdown string, markdown file, or HTML report.

    Args:
        report_path_or_content: File path or raw report string.

    Returns:
        The markdown text content of the report.
    """
    if os.path.isfile(report_path_or_content):
        with open(report_path_or_content, "r", encoding="utf-8", errors="ignore") as f:
            raw_content = f.read()
        if report_path_or_content.endswith(".html"):
            # Extract markdownText block from CodeBroker html format
            import re
            match = re.search(r"var\s+markdownText\s*=\s*`([\s\S]*?)`;", raw_content)
            if match:
                return match.group(1).replace(r"\`", "`")
            # Fallback: remove HTML tags
            clean_text = re.sub(r"<[^>]+>", " ", raw_content)
            return re.sub(r"\s+", " ", clean_text).strip()
        return raw_content
    return report_path_or_content


def compute_jax_quality_metrics(evaluation: CodeBrokerQualityReport) -> dict[str, float]:
    """Calculates weighted quality scores and statistics using JAX.

    Args:
        evaluation: The structured quality evaluation report.

    Returns:
        Dictionary of statistical score metrics computed via JAX.
    """
    dimensions = [
        evaluation.faithfulness,
        evaluation.completeness,
        evaluation.actionability,
        evaluation.scoring_calibration,
        evaluation.structure_adherence,
    ]
    scores = jnp.array([d.score for d in dimensions], dtype=jnp.float32)
    weights = jnp.array([d.weight for d in dimensions], dtype=jnp.float32)

    # Normalize weights using JAX
    weights = weights / jnp.sum(weights)

    weighted_score = jnp.dot(scores, weights)
    mean_score = jnp.mean(scores)
    std_score = jnp.std(scores)
    min_score = jnp.min(scores)
    max_score = jnp.max(scores)

    return {
        "weighted_overall_score": float(weighted_score),
        "mean_dimension_score": float(mean_score),
        "std_dimension_score": float(std_score),
        "min_dimension_score": float(min_score),
        "max_dimension_score": float(max_score),
    }


def build_polars_summary(
    evaluation: CodeBrokerQualityReport, jax_metrics: dict[str, float]
) -> pl.DataFrame:
    """Builds a structured Polars DataFrame summarizing the evaluation scores.

    Args:
        evaluation: The structured quality evaluation.
        jax_metrics: Metrics computed with JAX.

    Returns:
        Polars DataFrame containing dimension scores and contributions.
    """
    dims = [
        ("Faithfulness & Grounding", evaluation.faithfulness),
        ("Completeness & Coverage", evaluation.completeness),
        ("Actionability & Specificity", evaluation.actionability),
        ("Scoring Calibration", evaluation.scoring_calibration),
        ("Structure & Adherence", evaluation.structure_adherence),
    ]

    total_weight = sum(d.weight for _, d in dims)
    normalized_weights = [d.weight / total_weight for _, d in dims]

    df = pl.DataFrame({
        "dimension": [name for name, _ in dims],
        "raw_score": [float(d.score) for _, d in dims],
        "weight": [float(w) for w in normalized_weights],
        "weighted_points": [float(d.score * w) for (_, d), w in zip(dims, normalized_weights)],
        "strengths_count": [len(d.strengths) for _, d in dims],
        "weaknesses_count": [len(d.weaknesses) for _, d in dims],
        "rationale": [d.rationale for _, d in dims],
    })
    return df


# Tests


def test_load_source_code_single_file():
    """Tests loading a single Python file."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write("def sample_fn():\n    return 42\n")
        temp_path = tf.name

    try:
        loaded = load_source_code(temp_path)
        assert os.path.basename(temp_path) in loaded
        assert "sample_fn" in loaded[os.path.basename(temp_path)]
    finally:
        os.remove(temp_path)


def test_load_code_broker_report_html():
    """Tests extracting markdown report from CodeBroker HTML format."""
    html_content = """
    <html>
    <script>
        var md = window.markdownit();
        var markdownText = `# Code Assessment Report
## 1. Code Description
Test description`;
        document.getElementById('content').innerHTML = md.render(markdownText);
    </script>
    </html>
    """
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as tf:
        tf.write(html_content)
        temp_path = tf.name

    try:
        extracted = load_code_broker_report(temp_path)
        assert "# Code Assessment Report" in extracted
        assert "## 1. Code Description" in extracted
    finally:
        os.remove(temp_path)


def test_compute_jax_quality_metrics_and_polars():
    """Tests JAX mathematical operations and Polars summary table generation."""
    eval_rep = CodeBrokerQualityReport(
        faithfulness=DimensionScore(
            score=90.0, weight=0.25, rationale="Faithful to code", strengths=["Grounded"]
        ),
        completeness=DimensionScore(
            score=80.0, weight=0.20, rationale="Good coverage", strengths=["Covered core"]
        ),
        actionability=DimensionScore(
            score=85.0, weight=0.25, rationale="Actionable steps", strengths=["Clear steps"]
        ),
        scoring_calibration=DimensionScore(
            score=75.0, weight=0.15, rationale="Calibrated scores", weaknesses=["Slightly high"]
        ),
        structure_adherence=DimensionScore(
            score=95.0, weight=0.15, rationale="Followed 4 parts perfectly", strengths=["Clean markdown"]
        ),
        executive_summary="Solid report overall with minor calibration gaps.",
    )

    metrics = compute_jax_quality_metrics(eval_rep)
    assert 80.0 <= metrics["weighted_overall_score"] <= 90.0
    assert metrics["min_dimension_score"] == 75.0
    assert metrics["max_dimension_score"] == 95.0

    df = build_polars_summary(eval_rep, metrics)
    assert isinstance(df, pl.DataFrame)
    assert df.height == 5
    assert "dimension" in df.columns
    assert "raw_score" in df.columns
    assert "weighted_points" in df.columns
