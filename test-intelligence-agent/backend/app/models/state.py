"""LangGraph State Models for Test Intelligence Agent"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages


def add_logs(left: list, right: list) -> list:
    """Reducer to accumulate agent logs"""
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right


class AgentLog(TypedDict):
    """Log entry for agent telemetry"""
    agent_name: str
    step_number: int
    input_summary: str
    output_summary: str
    reasoning_summary: str | None
    status: Literal["success", "error", "skipped"]
    timestamp: str
    duration_seconds: float | None
    is_conditional: bool
    was_executed: bool


class RequirementField(TypedDict):
    """Extracted requirement field from platform specifications"""
    field_id: str
    field_name: str
    data_type: str
    mandatory: bool
    validation_rules: list[str]
    source_spec: str


class TestCase(TypedDict):
    """Generated test case"""
    test_id: str
    test_name: str
    description: str
    preconditions: list[str]
    test_steps: list[str]
    expected_result: str
    priority: Literal["Critical", "High", "Medium", "Low"]
    category: Literal["Functional", "Boundary", "Negative", "Compliance", "Integration"]
    requirement_refs: list[str]


class SyntheticDataRecord(TypedDict):
    """Schema-aware synthetic test data"""
    test_id: str
    data_payload: dict
    data_format: str


class TestResult(TypedDict):
    """Test execution result"""
    test_id: str
    test_name: str
    status: Literal["PASS", "FAIL", "SKIP", "ERROR"]
    execution_time_seconds: float
    actual_result: str
    error_message: str | None


class FailureAnalysis(TypedDict):
    """Root cause analysis for a failed test"""
    test_id: str
    root_cause: str
    category: Literal["Data Issue", "Logic Bug", "Configuration", "Environment", "Integration"]
    severity: Literal["Critical", "High", "Medium", "Low"]
    suggested_fix: str


class CodeRefactorSuggestion(TypedDict):
    """Suggested code fix for an identified bug"""
    test_id: str
    file_path: str
    original_code: str
    suggested_code: str
    explanation: str
    confidence: float


class ReportSection(TypedDict):
    """Section of a compliance report"""
    title: str
    content: str


class ComplianceReport(TypedDict):
    """GxP compliance report"""
    report_id: str
    platform: str
    generated_at: str
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    compliance_status: Literal["Compliant", "Non-Compliant", "Partially Compliant"]
    sections: list[ReportSection]


class TIAState(TypedDict):
    """
    Main state for the Test Intelligence Agent LangGraph workflow.
    Shared across all agents in the 7-step pipeline.
    """
    # Input
    session_id: str
    user_query: str
    conversation_history: Annotated[list, add_messages]
    selected_platform: str

    # Uploaded Document (optional)
    uploaded_document: str | None
    uploaded_document_name: str | None

    # Orchestrator Output
    platform_config: dict | None
    test_scope: str | None

    # Step 1: Requirement Agent
    requirements: list[RequirementField] | None
    requirement_summary: str | None

    # Step 2: Test Generation Agent
    test_cases: list[TestCase] | None
    test_generation_summary: str | None

    # Step 3: Synthetic Data Agent (CONDITIONAL)
    needs_synthetic_data: bool
    synthetic_data: list[SyntheticDataRecord] | None

    # Step 4: Execution Agent
    test_results: list[TestResult] | None
    execution_summary: str | None

    # Step 5: Failure Analysis Agent (CONDITIONAL)
    has_failures: bool
    failure_analyses: list[FailureAnalysis] | None

    # Step 6: Code Refactor Agent (CONDITIONAL)
    needs_code_refactor: bool
    refactor_suggestions: list[CodeRefactorSuggestion] | None

    # Step 7: Reporting Agent (ALWAYS)
    compliance_report: ComplianceReport | None
    final_answer: str | None

    # Visualization
    visualization_config: dict | None

    # Timing comparison (Manual vs Agent)
    timing_comparison: dict | None

    # Telemetry
    agent_logs: Annotated[list[AgentLog], add_logs]
