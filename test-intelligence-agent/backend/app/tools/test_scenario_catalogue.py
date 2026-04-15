"""
Test Scenario Catalogue for the Test Intelligence Agent.

Pre-built test scenarios for each deep platform. These scenarios serve as
templates that the agent can instantiate with specific parameters, or users
can select directly from the UI for quick test generation.
"""

TEST_SCENARIOS: dict = {
    # =========================================================================
    # 3DP  --  Drug Development Data Platform
    # =========================================================================
    "3dp": [
        {
            "scenario_id": "3dp-ctd-m3-substance",
            "name": "CTD Module 3 Substance Characterisation Validation",
            "description": (
                "Validates all fields in the Module 3.2.S (Drug Substance) section "
                "including substance name, manufacturer site, general properties, "
                "and control of drug substance specifications. Ensures mandatory "
                "fields are populated, data types conform to eCTD expectations, "
                "and cross-references to Module 2.3 QOS are consistent."
            ),
            "feature_area": "CTD Module 3.2.S",
            "typical_requirements": [
                "substance_name",
                "manufacturer",
                "batch_formula",
                "specification_limits",
                "description",
                "manufacturing_process",
            ],
            "expected_test_count": 48,
            "risk_level": "high",
        },
        {
            "scenario_id": "3dp-stability-integrity",
            "name": "Stability Study Data Integrity Check",
            "description": (
                "Verifies integrity and completeness of long-term, accelerated, "
                "and stress stability study records. Checks that time-point data "
                "is contiguous, specification limits are respected at each interval, "
                "and statistical trend analyses are reproducible."
            ),
            "feature_area": "CTD Module 3.2.P.8 (Stability)",
            "typical_requirements": [
                "substance_name",
                "stability_data",
                "specification_limits",
                "batch_formula",
            ],
            "expected_test_count": 36,
            "risk_level": "high",
        },
        {
            "scenario_id": "3dp-container-closure",
            "name": "Container Closure System Traceability",
            "description": (
                "Ensures container closure system records are fully traceable "
                "from raw material supplier through to finished product packaging. "
                "Validates material specifications, extractables/leachables data "
                "references, and compatibility study linkages."
            ),
            "feature_area": "CTD Module 3.2.P.7",
            "typical_requirements": [
                "container_closure",
                "specification_limits",
                "manufacturer",
                "description",
            ],
            "expected_test_count": 24,
            "risk_level": "medium",
        },
    ],

    # =========================================================================
    # BIKG  --  Biological Intelligence Knowledge Graph
    # =========================================================================
    "bikg": [
        {
            "scenario_id": "bikg-gene-disease-edges",
            "name": "Gene-Disease Relationship Edge Validation",
            "description": (
                "Validates the correctness of gene-disease association edges in "
                "the knowledge graph. Checks that evidence scores meet minimum "
                "thresholds, source databases are authoritative (OMIM, ClinVar, "
                "DisGeNET), and ontology terms resolve against the latest HPO "
                "and MONDO releases."
            ),
            "feature_area": "Gene-Disease Associations",
            "typical_requirements": [
                "source_entity",
                "target_entity",
                "relationship_type",
                "evidence_score",
                "source_database",
                "ontology_term",
            ],
            "expected_test_count": 42,
            "risk_level": "high",
        },
        {
            "scenario_id": "bikg-ppi-network",
            "name": "Protein-Protein Interaction Network Integrity",
            "description": (
                "Tests the integrity of protein-protein interaction (PPI) sub-graph "
                "by validating edge symmetry, UniProt accession format, interaction "
                "detection method codes (MI ontology), and evidence score "
                "distributions against expected statistical profiles."
            ),
            "feature_area": "Protein-Protein Interactions",
            "typical_requirements": [
                "source_entity",
                "target_entity",
                "relationship_type",
                "evidence_score",
                "species",
                "publication_reference",
            ],
            "expected_test_count": 38,
            "risk_level": "medium",
        },
        {
            "scenario_id": "bikg-ontology-alignment",
            "name": "Cross-Ontology Term Alignment Verification",
            "description": (
                "Verifies that ontology term mappings across MeSH, Gene Ontology, "
                "HPO, and ChEBI are consistent and up-to-date. Detects deprecated "
                "terms, broken cross-references, and ambiguous mappings that could "
                "affect downstream query accuracy."
            ),
            "feature_area": "Ontology Management",
            "typical_requirements": [
                "ontology_term",
                "source_database",
                "relationship_type",
            ],
            "expected_test_count": 30,
            "risk_level": "medium",
        },
    ],

    # =========================================================================
    # PATIENT SAFETY  --  Pharmacovigilance System
    # =========================================================================
    "patient_safety": [
        {
            "scenario_id": "ps-icsr-serious-ae",
            "name": "Serious Adverse Event ICSR Validation",
            "description": (
                "End-to-end validation of Individual Case Safety Reports for "
                "serious adverse events. Tests mandatory field population, MedDRA "
                "coding at LLT/PT/HLT/SOC levels, seriousness criteria flags, "
                "narrative quality checks, and E2B(R3) XML schema compliance "
                "for regulatory gateway submission."
            ),
            "feature_area": "ICSR Processing",
            "typical_requirements": [
                "patient_id",
                "drug_name",
                "adverse_event_term",
                "severity",
                "onset_date",
                "reporter_name",
                "report_type",
                "meddra_code",
                "outcome",
                "causality_assessment",
            ],
            "expected_test_count": 64,
            "risk_level": "critical",
        },
        {
            "scenario_id": "ps-e2b-xml-compliance",
            "name": "E2B(R3) XML Gateway Submission Compliance",
            "description": (
                "Validates that generated E2B(R3) XML files conform to ICH M2 "
                "specifications. Checks XML schema validation, mandatory element "
                "population, controlled vocabulary usage, character encoding, "
                "and attachment handling for FDA FAERS and EMA EudraVigilance "
                "gateway acceptance."
            ),
            "feature_area": "E2B(R3) Compliance",
            "typical_requirements": [
                "patient_id",
                "drug_name",
                "adverse_event_term",
                "meddra_code",
                "report_type",
            ],
            "expected_test_count": 52,
            "risk_level": "critical",
        },
        {
            "scenario_id": "ps-signal-detection",
            "name": "Signal Detection Data Quality Assurance",
            "description": (
                "Ensures data feeding into signal detection algorithms is "
                "complete and accurate. Validates case-level deduplication, "
                "MedDRA standardisation consistency, temporal alignment of "
                "reporting periods, and disproportionality analysis input "
                "data integrity."
            ),
            "feature_area": "Signal Detection",
            "typical_requirements": [
                "patient_id",
                "drug_name",
                "adverse_event_term",
                "meddra_code",
                "onset_date",
                "causality_assessment",
            ],
            "expected_test_count": 40,
            "risk_level": "high",
        },
    ],

    # =========================================================================
    # CLINICAL TRIALS  --  CDISC / SDTM Platform
    # =========================================================================
    "clinical_trials": [
        {
            "scenario_id": "ct-sdtm-domain-conformance",
            "name": "SDTM Domain Structure Conformance",
            "description": (
                "Validates that SDTM domains (DM, AE, LB, VS, CM, EX, etc.) "
                "conform to CDISC SDTM Implementation Guide v3.4. Checks "
                "variable names, labels, data types, controlled terminology, "
                "and sort key ordering. Runs Pinnacle 21 Community rules as "
                "a baseline and adds custom AstraZeneca-specific checks."
            ),
            "feature_area": "SDTM Conformance",
            "typical_requirements": [
                "studyid",
                "usubjid",
                "domain",
                "seq_variable",
                "visitnum",
                "dtc_variable",
                "testcd",
                "orres",
            ],
            "expected_test_count": 78,
            "risk_level": "high",
        },
        {
            "scenario_id": "ct-adam-derivation",
            "name": "ADaM Dataset Derivation Rule Validation",
            "description": (
                "Verifies that ADaM datasets (ADSL, ADAE, ADLB, ADTTE) are "
                "correctly derived from source SDTM domains. Checks population "
                "flags, baseline derivations, windowing logic, and traceability "
                "metadata in the analysis results dataset (define.xml)."
            ),
            "feature_area": "ADaM Derivations",
            "typical_requirements": [
                "studyid",
                "usubjid",
                "domain",
                "seq_variable",
            ],
            "expected_test_count": 56,
            "risk_level": "high",
        },
        {
            "scenario_id": "ct-define-xml-metadata",
            "name": "Define.xml Metadata Consistency Check",
            "description": (
                "Ensures define.xml accurately describes the submitted datasets. "
                "Validates that every variable in the datasets is documented, "
                "controlled terminology references are valid, computational "
                "methods are present for derived variables, and value-level "
                "metadata is complete."
            ),
            "feature_area": "Metadata Management",
            "typical_requirements": [
                "studyid",
                "domain",
                "testcd",
            ],
            "expected_test_count": 44,
            "risk_level": "medium",
        },
    ],

    # =========================================================================
    # HPC Environment  --  High Performance Computing
    # =========================================================================
    "hpc_environment": [
        {
            "scenario_id": "hpc-job-scheduling",
            "name": "Job Scheduling and Queue Fairness Validation",
            "description": (
                "Validates that SLURM/PBS job scheduling respects queue priorities, "
                "resource allocation policies, and fairness constraints across "
                "genomics, PKPD, and molecular simulation workloads."
            ),
            "feature_area": "Job Scheduling",
            "typical_requirements": [
                "Queue priority enforcement",
                "Resource allocation within limits",
                "Walltime enforcement",
                "Fair-share scheduling across users",
            ],
            "expected_test_count": 36,
            "risk_level": "high",
        },
        {
            "scenario_id": "hpc-reproducibility",
            "name": "Computational Reproducibility Verification",
            "description": (
                "Verifies that HPC pipeline outputs (checksums, numerical results) "
                "are deterministically reproducible across nodes, container versions, "
                "and execution environments using ReFrame sanity patterns."
            ),
            "feature_area": "Reproducibility",
            "typical_requirements": [
                "Output checksum matching",
                "Container image integrity",
                "Deterministic random seeds",
                "Cross-node consistency",
            ],
            "expected_test_count": 28,
            "risk_level": "high",
        },
        {
            "scenario_id": "hpc-metadata-scenario",
            "name": "Metadata-Scenario Consistency Testing",
            "description": (
                "Tests that execution metadata (run IDs, scenario parameters, "
                "pipeline versions) remain consistent across batch runs and that "
                "scenario parameter sets are version-controlled and approved."
            ),
            "feature_area": "Metadata-Scenario",
            "typical_requirements": [
                "Scenario ID references valid registry entries",
                "Parameter sets within defined bounds",
                "Version-controlled parameter changes",
                "Audit trail for parameter modifications",
            ],
            "expected_test_count": 32,
            "risk_level": "high",
        },
    ],
}


def get_scenarios_for_platform(platform_id: str) -> list[dict]:
    """Return the list of test scenarios for a given platform."""
    return TEST_SCENARIOS.get(platform_id, [])


def get_scenario_by_id(scenario_id: str) -> dict | None:
    """Look up a specific scenario by its unique scenario_id."""
    for scenarios in TEST_SCENARIOS.values():
        for scenario in scenarios:
            if scenario["scenario_id"] == scenario_id:
                return scenario
    return None


def list_all_scenario_ids() -> list[str]:
    """Return a flat list of all scenario IDs across platforms."""
    ids = []
    for scenarios in TEST_SCENARIOS.values():
        for scenario in scenarios:
            ids.append(scenario["scenario_id"])
    return sorted(ids)
