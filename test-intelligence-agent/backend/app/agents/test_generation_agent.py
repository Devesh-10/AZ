"""
Test Generation Agent (Step 2) for the Test Intelligence Agent.
Generates structured test cases from prioritised requirements.
Manual equivalent: ~3 days  |  Agent time: ~30 seconds
"""

import json
import time
from datetime import datetime

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings
from app.models.state import TIAState, AgentLog, TestCase

TEST_GEN_SYSTEM_PROMPT = """You are an expert Test Case Generator for AstraZeneca's pharmaceutical R&D platforms.

You operate in a GxP-regulated environment. Test cases you generate will be used for
Computer System Validation (CSV), IQ/OQ/PQ protocols, regulatory submissions
(FDA, EMA, PMDA), and integration into CI/CD pipelines and Xray test management workflows.
Traceability to requirements is mandatory.

Given a set of requirements and the test scope, generate **6 to 8** test cases that
provide comprehensive coverage. You MUST include the following category mix at minimum:

- 2 x Functional        (core business logic / happy path)
- 1 x Boundary          (edge values, limits, overflow)
- 1 x Negative          (invalid input, error handling, rejection)
- 1 x Compliance        (regulatory rule, audit trail, 21 CFR Part 11)
- 1 x Integration       (cross-system / cross-module interaction)
- 1 x Metadata-Scenario (metadata consistency, scenario parameter validation,
                          persona-based workflow paths, or environment-level config checks)

Additional test cases (up to 8 total) can be any category based on risk.

**Metadata-Scenario tests** verify that execution metadata (run IDs, scenario parameters,
pipeline versions, environment tags) remain consistent across runs. For HPC platforms,
these include ReFrame sanity checks, computational reproducibility, and SLURM/PBS
configuration integrity. For data platforms, these verify schema-metadata alignment
and scenario-based regression checks.

Output **strictly valid JSON** - an array of test case objects:

[
    {
        "test_id": "TC1",
        "test_name": "Short descriptive name",
        "description": "What this test verifies",
        "preconditions": ["Precondition 1", "Precondition 2"],
        "test_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
        "expected_result": "The expected outcome if the test passes",
        "priority": "Critical | High | Medium | Low",
        "category": "Functional | Boundary | Negative | Compliance | Integration | Metadata-Scenario",
        "requirement_refs": ["REQ-001", "REQ-003"]
    }
]

Guidelines:
- test_id must be sequential: TC1, TC2, TC3, ...
- Each test_steps list should have 3-6 concrete, executable steps.
- requirement_refs should reference field_id values from the provided requirements.
- priority: Critical for patient-safety / regulatory, High for core functionality,
  Medium for secondary features, Low for nice-to-have edge cases.
- Use realistic pharma terminology (batches, analytes, ICSRs, SDTM domains, etc.).
- For HPC platforms, include ReFrame environment checks and resource allocation tests.
- For data platforms, include schema-aware validation and metadata consistency tests.

Return ONLY the JSON array, no surrounding text.
"""


def test_generation_agent(state: TIAState) -> dict:
    """
    Test Generation Agent (Step 2).

    Takes requirements from Step 1 and generates 6-8 structured test cases
    with a guaranteed category mix: 2 Functional, 1 Boundary, 1 Negative,
    1 Compliance, 1 Integration (+ additional based on risk).

    Args:
        state: Current TIA state with requirements and test_scope.

    Returns:
        Partial state update with test_cases, test_generation_summary,
        and agent_logs.
    """
    start_time = time.time()
    requirements = state.get("requirements") or []
    test_scope = state.get("test_scope", "")
    platform_config = state.get("platform_config") or {}
    platform_name = platform_config.get("name", "Unknown Platform")

    try:
        # ------------------------------------------------------------------
        # 1. Build requirements context for the LLM
        # ------------------------------------------------------------------
        if requirements:
            req_text = "\n".join(
                f"- {r['field_id']}: {r['field_name']} "
                f"(type={r['data_type']}, mandatory={r['mandatory']}) "
                f"Rules: {', '.join(r['validation_rules'])}"
                for r in requirements
            )
        else:
            req_text = "(No explicit requirements provided - generate based on platform description and test scope.)"

        generation_prompt = (
            f"## Platform\n"
            f"Name: {platform_name}\n"
            f"Description: {platform_config.get('description', 'N/A')}\n"
            f"Tech Stack: {', '.join(platform_config.get('tech_stack', []))}\n\n"
            f"## Test Scope\n{test_scope}\n\n"
            f"## Requirements to Cover\n{req_text}\n\n"
            "Generate 6-8 test cases covering these requirements. "
            "Ensure the required category mix (2 Functional, 1 Boundary, "
            "1 Negative, 1 Compliance, 1 Integration, 1 Metadata-Scenario). "
            "Return ONLY a JSON array of test case objects."
        )

        # ------------------------------------------------------------------
        # 2. Invoke LLM
        # ------------------------------------------------------------------
        settings = get_settings()
        llm = ChatBedrockConverse(
            model=settings.test_gen_model,
            region_name=settings.aws_region,
            temperature=0.2,
            max_tokens=8192,
        )

        messages = [
            SystemMessage(content=TEST_GEN_SYSTEM_PROMPT),
            HumanMessage(content=generation_prompt),
        ]

        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        # ------------------------------------------------------------------
        # 3. Parse and normalise test cases
        # ------------------------------------------------------------------
        parsed = json.loads(raw)

        test_cases: list[TestCase] = []
        for i, item in enumerate(parsed, start=1):
            tc: TestCase = {
                "test_id": item.get("test_id", f"TC{i}"),
                "test_name": item.get("test_name", f"Test Case {i}"),
                "description": item.get("description", ""),
                "preconditions": item.get("preconditions", []),
                "test_steps": item.get("test_steps", []),
                "expected_result": item.get("expected_result", ""),
                "priority": item.get("priority", "Medium"),
                "category": item.get("category", "Functional"),
                "requirement_refs": item.get("requirement_refs", []),
            }
            # Normalise test_id to TC1, TC2, ... format
            tc["test_id"] = f"TC{i}"
            test_cases.append(tc)

        # ------------------------------------------------------------------
        # 4. Validate category mix
        # ------------------------------------------------------------------
        categories = [tc["category"] for tc in test_cases]
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1

        category_summary = ", ".join(
            f"{count} {cat}" for cat, count in sorted(category_counts.items())
        )

        test_generation_summary = (
            f"Generated {len(test_cases)} test cases for '{test_scope}' "
            f"on {platform_name}. Category breakdown: {category_summary}. "
            f"Covering {len(set(ref for tc in test_cases for ref in tc['requirement_refs']))} "
            f"unique requirements."
        )

        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Test Generation Agent",
            "step_number": 2,
            "input_summary": f"{len(requirements)} requirements, Scope: {test_scope[:60]}",
            "output_summary": f"{len(test_cases)} test cases generated ({category_summary})",
            "reasoning_summary": (
                f"Generated structured test cases with required category mix. "
                f"All test cases traceable to source requirements."
            ),
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }

        return {
            "test_cases": test_cases,
            "test_generation_summary": test_generation_summary,
            "agent_logs": [log_entry],
        }

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Test Generation Agent",
            "step_number": 2,
            "input_summary": f"{len(requirements)} requirements, Scope: {test_scope[:60]}",
            "output_summary": f"Error: {str(e)[:200]}",
            "reasoning_summary": "Unhandled exception during test case generation.",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }
        return {
            "test_cases": [],
            "test_generation_summary": f"Test generation failed: {str(e)[:200]}",
            "agent_logs": [log_entry],
        }
