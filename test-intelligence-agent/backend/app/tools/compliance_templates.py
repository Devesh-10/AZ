"""
GxP Compliance Report Templates for the Test Intelligence Agent.

These templates define the structure and content of the automated compliance
reports generated after each test execution cycle. Placeholders use Python
str.format() syntax: {placeholder_name}.
"""

REPORT_TEMPLATE: dict = {
    "executive_summary": (
        "EXECUTIVE SUMMARY\n"
        "=================\n\n"
        "Platform:            {platform_name}\n"
        "Report Date:         {report_date}\n"
        "Report ID:           {report_id}\n"
        "Execution Cycle:     {execution_cycle}\n"
        "Prepared By:         {prepared_by}\n\n"
        "This compliance report summarises the automated test execution results "
        "for the {platform_name} platform. A total of {total_tests} test cases "
        "were executed across {feature_areas_count} feature areas, achieving an "
        "overall pass rate of {overall_pass_rate}%.\n\n"
        "Critical findings:   {critical_findings_count}\n"
        "Major findings:      {major_findings_count}\n"
        "Minor findings:      {minor_findings_count}\n\n"
        "Compliance determination: {compliance_status}\n\n"
        "The agent-driven test cycle completed in {total_execution_time} seconds, "
        "compared to an estimated {manual_equivalent_hours} hours for equivalent "
        "manual testing effort ({efficiency_gain_factor}x efficiency gain).\n"
    ),

    "requirements_coverage": (
        "REQUIREMENTS COVERAGE ANALYSIS\n"
        "==============================\n\n"
        "Total requirements in scope:    {total_requirements}\n"
        "Requirements with test coverage: {covered_requirements}\n"
        "Requirements coverage rate:      {coverage_rate}%\n"
        "Untested requirements:           {untested_requirements}\n\n"
        "Coverage Breakdown by Module:\n"
        "{module_coverage_table}\n\n"
        "Requirements Risk Distribution:\n"
        "  Critical: {critical_req_count} ({critical_req_pct}%)\n"
        "  High:     {high_req_count} ({high_req_pct}%)\n"
        "  Medium:   {medium_req_count} ({medium_req_pct}%)\n"
        "  Low:      {low_req_count} ({low_req_pct}%)\n\n"
        "Traceability Matrix Reference: {traceability_matrix_ref}\n"
    ),

    "test_execution_results": (
        "TEST EXECUTION RESULTS\n"
        "======================\n\n"
        "Execution Environment:  {execution_environment}\n"
        "Start Time:             {execution_start_time}\n"
        "End Time:               {execution_end_time}\n"
        "Total Duration:         {total_duration_seconds} seconds\n\n"
        "Result Summary:\n"
        "  Total Test Cases:  {total_tests}\n"
        "  Passed:            {passed_count} ({pass_rate}%)\n"
        "  Failed:            {failed_count} ({fail_rate}%)\n"
        "  Skipped:           {skipped_count} ({skip_rate}%)\n"
        "  Blocked:           {blocked_count} ({blocked_rate}%)\n\n"
        "Results by Feature Area:\n"
        "{feature_area_results_table}\n\n"
        "Results by Risk Level:\n"
        "{risk_level_results_table}\n\n"
        "Test Case Detail Listing:\n"
        "{test_case_detail_listing}\n"
    ),

    "failure_analysis": (
        "FAILURE ANALYSIS\n"
        "================\n\n"
        "Total Failures:        {total_failures}\n"
        "Unique Failure Modes:  {unique_failure_modes}\n"
        "Regression Failures:   {regression_failure_count}\n"
        "New Failures:          {new_failure_count}\n\n"
        "Root Cause Classification:\n"
        "  Data Quality:        {data_quality_failures} ({data_quality_pct}%)\n"
        "  Schema Violation:    {schema_violation_failures} ({schema_violation_pct}%)\n"
        "  Business Logic:      {business_logic_failures} ({business_logic_pct}%)\n"
        "  Integration:         {integration_failures} ({integration_pct}%)\n"
        "  Environment:         {environment_failures} ({environment_pct}%)\n\n"
        "Top Failure Patterns:\n"
        "{top_failure_patterns}\n\n"
        "Failure Details:\n"
        "{failure_detail_listing}\n"
    ),

    "remediation_plan": (
        "REMEDIATION PLAN\n"
        "================\n\n"
        "The following remediation actions are recommended based on the failure "
        "analysis. Items are prioritised by risk impact and regulatory urgency.\n\n"
        "Immediate Actions (within 24 hours):\n"
        "{immediate_actions}\n\n"
        "Short-Term Actions (within 1 week):\n"
        "{short_term_actions}\n\n"
        "Long-Term Actions (within 1 quarter):\n"
        "{long_term_actions}\n\n"
        "Estimated Remediation Effort: {remediation_effort_hours} hours\n"
        "Remediation Owner:            {remediation_owner}\n"
        "Target Completion Date:       {target_completion_date}\n"
        "Re-validation Required:       {revalidation_required}\n"
    ),

    "compliance_determination": (
        "COMPLIANCE DETERMINATION\n"
        "========================\n\n"
        "Regulatory Framework:      {regulatory_framework}\n"
        "Applicable Guidelines:     {applicable_guidelines}\n"
        "Validation Level:          {validation_level}\n\n"
        "Determination: {compliance_determination}\n\n"
        "Rationale:\n"
        "{compliance_rationale}\n\n"
        "Conditions / Caveats:\n"
        "{compliance_conditions}\n\n"
        "This determination is based on the test results obtained during "
        "execution cycle {execution_cycle} on {report_date}. The overall "
        "pass rate of {overall_pass_rate}% {meets_or_fails} the minimum "
        "acceptable threshold of {minimum_pass_threshold}% for "
        "{platform_name}.\n\n"
        "Approved By:       {approver_name}\n"
        "Approval Date:     {approval_date}\n"
        "Digital Signature:  {digital_signature_ref}\n"
    ),

    "evidence_artifacts": (
        "EVIDENCE ARTIFACTS\n"
        "==================\n\n"
        "The following artifacts are attached or referenced as evidence "
        "supporting this compliance report.\n\n"
        "Test Execution Logs:\n"
        "  Location:  {execution_log_path}\n"
        "  Hash:      {execution_log_hash}\n"
        "  Size:      {execution_log_size}\n\n"
        "Synthetic Test Data:\n"
        "  Location:  {synthetic_data_path}\n"
        "  Hash:      {synthetic_data_hash}\n"
        "  Records:   {synthetic_data_record_count}\n\n"
        "Requirements Traceability Matrix:\n"
        "  Location:  {traceability_matrix_path}\n"
        "  Hash:      {traceability_matrix_hash}\n\n"
        "Screenshots / Visual Evidence:\n"
        "{visual_evidence_listing}\n\n"
        "Audit Trail:\n"
        "  Location:  {audit_trail_path}\n"
        "  Entries:   {audit_trail_entry_count}\n"
        "  Period:    {audit_trail_start} to {audit_trail_end}\n\n"
        "All artifacts are stored in the GxP-validated document management "
        "system and are subject to 21 CFR Part 11 electronic record controls.\n"
    ),

    "regulatory_references": (
        "REGULATORY REFERENCES\n"
        "=====================\n\n"
        "The following regulatory guidelines and standards were applied "
        "during test design, execution, and compliance evaluation:\n\n"
        "ICH Guidelines:\n"
        "  - ICH E6(R2): Good Clinical Practice\n"
        "  - ICH E2B(R3): Electronic Transmission of ICSRs\n"
        "  - ICH M2: Electronic Standards for Regulatory Submissions\n"
        "  - ICH M4: Common Technical Document (CTD)\n"
        "  - ICH Q7: Good Manufacturing Practice for APIs\n\n"
        "FDA Regulations:\n"
        "  - 21 CFR Part 11: Electronic Records; Electronic Signatures\n"
        "  - 21 CFR Part 211: Current Good Manufacturing Practice\n"
        "  - 21 CFR Part 312: Investigational New Drug Application\n"
        "  - 21 CFR Part 314: Applications for FDA Approval\n\n"
        "EMA Guidelines:\n"
        "  - EMA/873138/2011: GVP Module VI - Periodic Safety Update Reports\n"
        "  - EMA/541760/2011: GVP Module IX - Signal Management\n\n"
        "CDISC Standards:\n"
        "  - SDTM Implementation Guide v3.4\n"
        "  - ADaM Implementation Guide v1.3\n"
        "  - Define-XML v2.1\n"
        "  - Controlled Terminology {ct_package_version}\n\n"
        "Industry Standards:\n"
        "  - GAMP 5: A Risk-Based Approach to Compliant GxP Computerized Systems\n"
        "  - IEEE 829: Standard for Software Test Documentation\n"
        "  - ISO/IEC 25010: Systems and Software Quality Requirements\n\n"
        "Platform-Specific References:\n"
        "{platform_specific_references}\n"
    ),
}


def get_template_section(section_name: str) -> str | None:
    """Return a single report template section by name."""
    return REPORT_TEMPLATE.get(section_name)


def get_all_section_names() -> list[str]:
    """Return the ordered list of report section names."""
    return list(REPORT_TEMPLATE.keys())


def render_section(section_name: str, **kwargs) -> str:
    """
    Render a report section by filling in the placeholders.

    Any placeholders not supplied in kwargs will be left as-is
    (wrapped in curly braces) so partial rendering is supported.
    """
    template = REPORT_TEMPLATE.get(section_name)
    if template is None:
        raise ValueError(f"Unknown report section: {section_name}")

    # Use safe substitution: missing keys are left as {key}
    class SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"

    return template.format_map(SafeDict(**kwargs))
