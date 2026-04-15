"""
Synthetic Data Agent (Step 3 - CONDITIONAL) for the Test Intelligence Agent.
Generates schema-conforming fake data for each test case when needed.
Manual equivalent: ~1 day  |  Agent time: ~15 seconds
"""

import json
import time
from datetime import datetime
from pathlib import Path

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings
from app.models.state import TIAState, AgentLog, SyntheticDataRecord

SYNTHETIC_DATA_SYSTEM_PROMPT = """You are a Synthetic Data Engineer for AstraZeneca's Test Intelligence Agent.

You operate in a GxP-regulated pharmaceutical R&D environment. Your job is to generate
realistic, schema-conforming synthetic test data for each test case. The data must:

1. Be realistic enough to exercise the test case's logic paths.
2. Conform to any provided schema definitions (field types, formats, constraints).
3. Include both valid and boundary/edge-case values as appropriate for the test category.
4. NEVER use real patient data, real drug names, or real trial identifiers.
5. Use pharma-plausible dummy values (e.g. "AZD-XXXX" for compound IDs,
   "STUDY-001" for trial IDs, "MedDRA PT: Headache" for adverse events).

For each test case, generate a data payload that the execution agent can use.

Output **strictly valid JSON** - an array of synthetic data records:

[
    {
        "test_id": "TC1",
        "data_payload": {
            "field_1": "value_1",
            "field_2": 42,
            "field_3": true
        },
        "data_format": "json"
    }
]

The data_payload should contain all fields needed to execute the corresponding test case.
Include realistic values that match the test's category:
- Functional tests: valid, representative data
- Boundary tests: edge values (min, max, empty strings, very long strings)
- Negative tests: invalid data (wrong types, null where mandatory, out-of-range)
- Compliance tests: data that exercises audit trail / regulatory fields
- Integration tests: data spanning multiple entities / cross-references

Return ONLY the JSON array, no surrounding text.
"""


def _load_schemas(data_dir: str) -> dict | None:
    """
    Attempt to load schemas.json from the platform's data directory.
    Returns the parsed JSON or None if the file is not found.
    """
    schema_path = Path(__file__).parent.parent.parent / data_dir / "schemas.json"
    if not schema_path.exists():
        return None

    try:
        with open(schema_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def synthetic_data_agent(state: TIAState) -> dict:
    """
    Synthetic Data Agent (Step 3 - CONDITIONAL).

    Only runs when needs_synthetic_data is True. Loads schema definitions
    from the platform's data directory when available and uses LLM to
    generate schema-conforming fake data for each test case.

    Args:
        state: Current TIA state with test_cases, platform_config, and
               needs_synthetic_data flag.

    Returns:
        Partial state update with synthetic_data and agent_logs.
    """
    start_time = time.time()
    needs_synthetic_data = state.get("needs_synthetic_data", False)
    test_cases = state.get("test_cases") or []
    platform_config = state.get("platform_config") or {}
    platform_name = platform_config.get("name", "Unknown Platform")
    test_scope = state.get("test_scope", "")

    # ------------------------------------------------------------------
    # Guard: skip if not needed
    # ------------------------------------------------------------------
    if not needs_synthetic_data:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Synthetic Data Agent",
            "step_number": 3,
            "input_summary": f"needs_synthetic_data=False",
            "output_summary": "Skipped - synthetic data not required",
            "reasoning_summary": "Orchestrator determined synthetic data is not needed for this test run.",
            "status": "skipped",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": False,
        }
        return {
            "synthetic_data": [],
            "agent_logs": [log_entry],
        }

    if not test_cases:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Synthetic Data Agent",
            "step_number": 3,
            "input_summary": "No test cases provided",
            "output_summary": "Skipped - no test cases to generate data for",
            "reasoning_summary": "Upstream test generation produced no test cases.",
            "status": "skipped",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": False,
        }
        return {
            "synthetic_data": [],
            "agent_logs": [log_entry],
        }

    try:
        # ------------------------------------------------------------------
        # 1. Load schema definitions if available
        # ------------------------------------------------------------------
        data_dir = platform_config.get("data_dir", "")
        schemas = _load_schemas(data_dir) if data_dir else None

        schema_context = ""
        if schemas:
            schema_context = (
                "\n## Schema Definitions\n"
                "Use these schemas to generate conforming data:\n"
                f"```json\n{json.dumps(schemas, indent=2)[:3000]}\n```\n"
            )

        # ------------------------------------------------------------------
        # 2. Build test case context
        # ------------------------------------------------------------------
        tc_text = "\n".join(
            f"- {tc['test_id']}: {tc['test_name']} "
            f"(Category: {tc['category']}, Priority: {tc['priority']})\n"
            f"  Description: {tc['description']}\n"
            f"  Expected Result: {tc['expected_result']}"
            for tc in test_cases
        )

        generation_prompt = (
            f"## Platform\n"
            f"Name: {platform_name}\n"
            f"Description: {platform_config.get('description', 'N/A')}\n\n"
            f"## Test Scope\n{test_scope}\n\n"
            f"{schema_context}"
            f"## Test Cases Requiring Data\n{tc_text}\n\n"
            f"Generate synthetic data payloads for ALL {len(test_cases)} test cases. "
            "Match the data to each test's category (valid data for Functional, "
            "edge values for Boundary, invalid data for Negative, etc.). "
            "Return ONLY a JSON array of synthetic data records."
        )

        # ------------------------------------------------------------------
        # 3. Invoke LLM
        # ------------------------------------------------------------------
        settings = get_settings()
        llm = ChatBedrockConverse(
            model=settings.synthetic_data_model,
            region_name=settings.aws_region,
            temperature=0.3,
            max_tokens=8192,
        )

        messages = [
            SystemMessage(content=SYNTHETIC_DATA_SYSTEM_PROMPT),
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
        # 4. Parse and normalise
        # ------------------------------------------------------------------
        parsed = json.loads(raw)

        synthetic_data: list[SyntheticDataRecord] = []
        for i, item in enumerate(parsed):
            record: SyntheticDataRecord = {
                "test_id": item.get("test_id", test_cases[i]["test_id"] if i < len(test_cases) else f"TC{i+1}"),
                "data_payload": item.get("data_payload", {}),
                "data_format": item.get("data_format", "json"),
            }
            synthetic_data.append(record)

        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Synthetic Data Agent",
            "step_number": 3,
            "input_summary": f"{len(test_cases)} test cases, Schema: {'loaded' if schemas else 'generated'}",
            "output_summary": f"{len(synthetic_data)} synthetic data records generated",
            "reasoning_summary": (
                f"Generated schema-conforming synthetic data for {len(synthetic_data)} test cases. "
                f"Schema source: {'platform schemas.json' if schemas else 'LLM-inferred from platform description'}."
            ),
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": True,
        }

        return {
            "synthetic_data": synthetic_data,
            "agent_logs": [log_entry],
        }

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Synthetic Data Agent",
            "step_number": 3,
            "input_summary": f"{len(test_cases)} test cases",
            "output_summary": f"Error: {str(e)[:200]}",
            "reasoning_summary": "Unhandled exception during synthetic data generation.",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": True,
        }
        return {
            "synthetic_data": [],
            "agent_logs": [log_entry],
        }
