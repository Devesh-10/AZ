"""
Requirement Agent (Step 1) for the Test Intelligence Agent.
Extracts and prioritises platform requirements from CSV data or LLM generation.
Manual equivalent: ~3 days  |  Agent time: ~30 seconds
"""

import csv
import json
import time
from datetime import datetime
from pathlib import Path

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings
from app.models.state import TIAState, AgentLog, RequirementField

REQUIREMENT_SYSTEM_PROMPT = """You are a Requirements Analyst for AstraZeneca's Test Intelligence Agent.

You work in a GxP-regulated pharmaceutical R&D environment where data integrity,
regulatory compliance (FDA 21 CFR Part 11, EU Annex 11, ICH guidelines), and patient
safety are paramount.

Given a platform description and the specific test scope, extract or generate a set of
**testable requirements**. Each requirement should represent a discrete, verifiable
field or rule that must be validated.

Output **strictly valid JSON** - an array of requirement objects:

[
    {
        "field_id": "REQ-001",
        "field_name": "Human-readable field or rule name",
        "data_type": "string | integer | float | date | boolean | enum | object",
        "mandatory": true,
        "validation_rules": ["Rule 1", "Rule 2"],
        "source_spec": "Specification or regulation this derives from"
    }
]

Guidelines:
- Generate 8-12 requirements that cover the test scope comprehensively.
- Include at least one requirement per category: data integrity, business logic,
  regulatory compliance, and boundary validation.
- Use realistic pharma R&D terminology (MedDRA, CDISC, ICH, GxP, CTD, etc.).
- Each validation_rules list should have 1-3 concrete, testable rules.
- field_id format: REQ-001, REQ-002, ...

Return ONLY the JSON array, no surrounding text.
"""


def _load_requirements_csv(data_dir: str) -> list[dict] | None:
    """
    Attempt to load requirements.csv from the platform's data directory.
    Returns a list of row dicts or None if the file is not found.
    """
    csv_path = Path(__file__).parent.parent.parent / data_dir / "requirements.csv"
    if not csv_path.exists():
        return None

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows if rows else None


def _csv_rows_to_requirements(rows: list[dict]) -> list[RequirementField]:
    """Convert raw CSV rows into RequirementField typed-dicts."""
    requirements: list[RequirementField] = []
    for i, row in enumerate(rows, start=1):
        req: RequirementField = {
            "field_id": row.get("field_id", f"REQ-{i:03d}"),
            "field_name": row.get("field_name", row.get("name", f"Requirement {i}")),
            "data_type": row.get("data_type", "string"),
            "mandatory": str(row.get("mandatory", "true")).lower() in ("true", "1", "yes"),
            "validation_rules": [
                r.strip()
                for r in row.get("validation_rules", "").split("|")
                if r.strip()
            ],
            "source_spec": row.get("source_spec", "Platform Specification"),
        }
        requirements.append(req)
    return requirements


def requirement_agent(state: TIAState) -> dict:
    """
    Requirement Agent (Step 1).

    Loads requirements from CSV when available, otherwise uses LLM to generate
    requirements from the platform description and test scope. Prioritises
    requirements relevant to the current test scope.

    Args:
        state: Current TIA state with platform_config and test_scope.

    Returns:
        Partial state update with requirements, requirement_summary,
        and agent_logs.
    """
    start_time = time.time()
    platform_config = state.get("platform_config") or {}
    test_scope = state.get("test_scope", "")
    platform_name = platform_config.get("name", "Unknown Platform")

    try:
        # ------------------------------------------------------------------
        # Check for uploaded document (highest priority)
        # ------------------------------------------------------------------
        uploaded_document = state.get("uploaded_document")
        uploaded_document_name = state.get("uploaded_document_name", "uploaded file")

        # ------------------------------------------------------------------
        # 1. Attempt to load requirements from CSV
        # ------------------------------------------------------------------
        data_dir = platform_config.get("data_dir", "")
        csv_rows = _load_requirements_csv(data_dir) if data_dir else None

        settings = get_settings()
        llm = ChatBedrockConverse(
            model=settings.requirement_model,
            region_name=settings.aws_region,
            temperature=0.1,
            max_tokens=4096,
        )

        if uploaded_document:
            # ---------------------------------------------------------------
            # UPLOADED DOCUMENT: Extract requirements via LLM (top priority)
            # ---------------------------------------------------------------
            extract_prompt = (
                f"## Uploaded Document\n"
                f"Filename: {uploaded_document_name}\n\n"
                f"## Document Content\n{uploaded_document[:8000]}\n\n"
                f"## Platform Context\n"
                f"Name: {platform_name}\n"
                f"Description: {platform_config.get('description', 'N/A')}\n"
                f"Test Domains: {', '.join(platform_config.get('test_domains', []))}\n\n"
                f"## Test Scope\n{test_scope}\n\n"
                "Extract all testable requirements from the uploaded document. "
                "Map each requirement to a field that can be validated in the context "
                "of the platform above. Return 8-15 requirements.\n"
                "Return ONLY a JSON array of requirement objects."
            )

            messages = [
                SystemMessage(content=REQUIREMENT_SYSTEM_PROMPT),
                HumanMessage(content=extract_prompt),
            ]

            response = llm.invoke(messages)
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

            parsed = json.loads(raw)
            requirements = []
            for i, item in enumerate(parsed, start=1):
                req: RequirementField = {
                    "field_id": item.get("field_id", f"REQ-{i:03d}"),
                    "field_name": item.get("field_name", f"Requirement {i}"),
                    "data_type": item.get("data_type", "string"),
                    "mandatory": bool(item.get("mandatory", True)),
                    "validation_rules": item.get("validation_rules", []),
                    "source_spec": item.get(
                        "source_spec",
                        f"Extracted from {uploaded_document_name}",
                    ),
                }
                requirements.append(req)

            source_method = f"Extracted from uploaded document: {uploaded_document_name}"

        elif csv_rows:
            # CSV found -- convert rows, then use LLM to filter/prioritise
            all_requirements = _csv_rows_to_requirements(csv_rows)

            filter_prompt = (
                f"Given the test scope '{test_scope}' on platform '{platform_name}', "
                f"I have {len(all_requirements)} requirements loaded from CSV.\n\n"
                f"Requirements:\n"
                + "\n".join(
                    f"- {r['field_id']}: {r['field_name']} ({r['data_type']}, "
                    f"mandatory={r['mandatory']}) - {', '.join(r['validation_rules'])}"
                    for r in all_requirements
                )
                + "\n\nReturn a JSON array of the field_ids that are most relevant to "
                "the test scope, ordered by priority (most critical first). "
                "Include at least 6 and at most 12 items.\n"
                "Output format: [\"REQ-001\", \"REQ-003\", ...]"
            )

            messages = [
                SystemMessage(content="You are a pharma R&D test prioritisation expert. Return only valid JSON."),
                HumanMessage(content=filter_prompt),
            ]

            response = llm.invoke(messages)
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

            try:
                priority_ids = json.loads(raw)
                # Reorder requirements by LLM priority
                id_order = {fid: idx for idx, fid in enumerate(priority_ids)}
                requirements = sorted(
                    [r for r in all_requirements if r["field_id"] in id_order],
                    key=lambda r: id_order.get(r["field_id"], 999),
                )
                # If LLM returned fewer than all, append remaining
                remaining = [r for r in all_requirements if r["field_id"] not in id_order]
                requirements.extend(remaining)
            except json.JSONDecodeError:
                # Fallback: use all CSV requirements as-is
                requirements = all_requirements

            source_method = "CSV + LLM prioritisation"

        else:
            # No CSV found -- generate requirements via LLM
            generation_prompt = (
                f"## Platform\n"
                f"Name: {platform_name}\n"
                f"Description: {platform_config.get('description', 'N/A')}\n"
                f"Tech Stack: {', '.join(platform_config.get('tech_stack', []))}\n"
                f"Test Domains: {', '.join(platform_config.get('test_domains', []))}\n\n"
                f"## Test Scope\n{test_scope}\n\n"
                "Generate 8-12 testable requirements for this scope. "
                "Return ONLY a JSON array of requirement objects."
            )

            messages = [
                SystemMessage(content=REQUIREMENT_SYSTEM_PROMPT),
                HumanMessage(content=generation_prompt),
            ]

            response = llm.invoke(messages)
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

            parsed = json.loads(raw)
            requirements = []
            for i, item in enumerate(parsed, start=1):
                req: RequirementField = {
                    "field_id": item.get("field_id", f"REQ-{i:03d}"),
                    "field_name": item.get("field_name", f"Requirement {i}"),
                    "data_type": item.get("data_type", "string"),
                    "mandatory": bool(item.get("mandatory", True)),
                    "validation_rules": item.get("validation_rules", []),
                    "source_spec": item.get("source_spec", "LLM-generated"),
                }
                requirements.append(req)

            source_method = "LLM generation (no CSV available)"

        # ------------------------------------------------------------------
        # 2. Build summary
        # ------------------------------------------------------------------
        mandatory_count = sum(1 for r in requirements if r["mandatory"])
        requirement_summary = (
            f"Extracted {len(requirements)} requirements for '{test_scope}' "
            f"on {platform_name}. {mandatory_count} mandatory, "
            f"{len(requirements) - mandatory_count} optional. "
            f"Source: {source_method}."
        )

        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Requirement Agent",
            "step_number": 1,
            "input_summary": f"Platform: {platform_name}, Scope: {test_scope[:80]}",
            "output_summary": f"{len(requirements)} requirements extracted ({source_method})",
            "reasoning_summary": (
                f"Loaded requirements via {source_method}. "
                f"{mandatory_count}/{len(requirements)} marked mandatory."
            ),
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }

        return {
            "requirements": requirements,
            "requirement_summary": requirement_summary,
            "agent_logs": [log_entry],
        }

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Requirement Agent",
            "step_number": 1,
            "input_summary": f"Platform: {platform_name}, Scope: {test_scope[:80]}",
            "output_summary": f"Error: {str(e)[:200]}",
            "reasoning_summary": "Unhandled exception during requirement extraction.",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }
        return {
            "requirements": [],
            "requirement_summary": f"Requirement extraction failed: {str(e)[:200]}",
            "agent_logs": [log_entry],
        }
