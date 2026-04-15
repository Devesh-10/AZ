"""
Orchestrator Agent (Step 0) for the Test Intelligence Agent.
Routes user queries by determining test scope and platform configuration.
Uses LLM to understand what the user wants to test on the selected platform.
"""

import json
import time
from datetime import datetime

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings
from app.models.state import TIAState, AgentLog
from app.tools.platform_catalogue import PLATFORM_CATALOGUE

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Orchestrator for the AstraZeneca Test Intelligence Agent.

You operate within a GxP-regulated pharmaceutical R&D environment. Your job is to analyse
the user's request alongside the selected platform definition and determine:

1. **test_scope** - A concise description of the specific area, feature, or domain to test
   on this platform (e.g. "CTD Module 3 substance characterisation field validation",
   "ICSR serious adverse event submission workflow", "HPC job scheduling and ReFrame
   environment-level verification").

2. **needs_synthetic_data** - Whether the tests require schema-aware synthetic data to be
   generated. Set to true for platforms that manage structured records (batch data, ICSRs,
   SDTM domains, knowledge-graph triples, HPC job execution records, metadata-scenario
   parameters). Set to false only when tests are purely configuration or documentation checks.

Key considerations for environment-level test selection:
- For HPC platforms: select relevant ReFrame test suites, SLURM/PBS scheduling checks,
  computational reproducibility tests, and metadata-scenario consistency validations.
- For data platforms: select schema-aware field validations, metadata structure checks,
  and cross-platform referential integrity tests.
- Always consider which environment (production, staging, development) the tests target.

Given the platform metadata and the user request, output **strictly valid JSON** with exactly
two keys:

{
    "test_scope": "<string describing what to test>",
    "needs_synthetic_data": <true | false>
}

Do NOT include any text outside the JSON object.
"""


def orchestrator_agent(state: TIAState) -> dict:
    """
    Orchestrator Agent (Step 0).

    Loads the platform configuration from the catalogue, uses LLM to determine
    test scope, and decides whether synthetic data generation is needed.

    Args:
        state: Current TIA state with user_query and selected_platform.

    Returns:
        Partial state update with platform_config, test_scope,
        needs_synthetic_data, and agent_logs.
    """
    start_time = time.time()
    user_query = state["user_query"]
    selected_platform = state["selected_platform"]

    try:
        # ------------------------------------------------------------------
        # 1. Load platform configuration from catalogue
        # ------------------------------------------------------------------
        platform_config = PLATFORM_CATALOGUE.get(selected_platform)
        if platform_config is None:
            duration = round(time.time() - start_time, 2)
            log_entry: AgentLog = {
                "agent_name": "Orchestrator",
                "step_number": 0,
                "input_summary": f"Platform: {selected_platform}, Query: {user_query[:100]}",
                "output_summary": f"Platform '{selected_platform}' not found in catalogue",
                "reasoning_summary": "Platform ID did not match any entry in PLATFORM_CATALOGUE.",
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": duration,
                "is_conditional": False,
                "was_executed": True,
            }
            return {
                "platform_config": None,
                "test_scope": None,
                "needs_synthetic_data": False,
                "agent_logs": [log_entry],
            }

        # ------------------------------------------------------------------
        # 2. Ask LLM to determine test scope and data needs
        # ------------------------------------------------------------------
        settings = get_settings()
        llm = ChatBedrockConverse(
            model=settings.orchestrator_model,
            region_name=settings.aws_region,
            temperature=0.1,
            max_tokens=4096,
        )

        platform_summary = (
            f"Platform: {platform_config['name']}\n"
            f"Description: {platform_config['description']}\n"
            f"Depth: {platform_config['depth']}\n"
            f"Tech Stack: {', '.join(platform_config.get('tech_stack', []))}\n"
            f"Test Domains: {', '.join(platform_config.get('test_domains', []))}\n"
        )

        messages = [
            SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"## Platform Metadata\n{platform_summary}\n\n"
                    f"## User Request\n{user_query}\n\n"
                    "Determine the test scope and whether synthetic data is needed. "
                    "Respond with JSON only."
                )
            ),
        ]

        response = llm.invoke(messages)
        raw_content = response.content.strip()

        # ------------------------------------------------------------------
        # 3. Parse LLM JSON response
        # ------------------------------------------------------------------
        # Strip markdown fences if present
        if raw_content.startswith("```"):
            raw_content = raw_content.split("\n", 1)[1] if "\n" in raw_content else raw_content[3:]
        if raw_content.endswith("```"):
            raw_content = raw_content.rsplit("```", 1)[0]
        raw_content = raw_content.strip()

        parsed = json.loads(raw_content)
        test_scope = parsed.get("test_scope", user_query)
        needs_synthetic_data = bool(parsed.get("needs_synthetic_data", True))

        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Orchestrator",
            "step_number": 0,
            "input_summary": f"Platform: {platform_config['name']}, Query: {user_query[:80]}",
            "output_summary": f"Scope: {test_scope[:120]}, Synthetic data: {needs_synthetic_data}",
            "reasoning_summary": (
                f"Analysed platform '{platform_config['name']}' against user intent. "
                f"Identified test scope and data requirements via LLM."
            ),
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }

        return {
            "platform_config": platform_config,
            "test_scope": test_scope,
            "needs_synthetic_data": needs_synthetic_data,
            "agent_logs": [log_entry],
        }

    except json.JSONDecodeError as e:
        duration = round(time.time() - start_time, 2)
        # Fallback: derive scope from user query directly
        fallback_scope = user_query
        log_entry: AgentLog = {
            "agent_name": "Orchestrator",
            "step_number": 0,
            "input_summary": f"Platform: {selected_platform}, Query: {user_query[:100]}",
            "output_summary": f"JSON parse error; fell back to user query as scope",
            "reasoning_summary": f"LLM response was not valid JSON: {str(e)[:200]}",
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }
        return {
            "platform_config": PLATFORM_CATALOGUE.get(selected_platform),
            "test_scope": fallback_scope,
            "needs_synthetic_data": True,
            "agent_logs": [log_entry],
        }

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Orchestrator",
            "step_number": 0,
            "input_summary": f"Platform: {selected_platform}, Query: {user_query[:100]}",
            "output_summary": f"Error: {str(e)[:200]}",
            "reasoning_summary": "Unhandled exception during orchestration.",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }
        return {
            "platform_config": PLATFORM_CATALOGUE.get(selected_platform),
            "test_scope": user_query,
            "needs_synthetic_data": True,
            "agent_logs": [log_entry],
        }
