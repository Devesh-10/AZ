"""
Platform Catalogue for the Test Intelligence Agent.

Defines all 9 platforms under test: 5 "deep" platforms with full test generation
capabilities and 4 "visual" platforms with dashboard-level metrics and monitoring.
"""

PLATFORM_CATALOGUE: dict = {
    # =========================================================================
    # DEEP PLATFORMS  (full test-generation, synthetic data, compliance reports)
    # =========================================================================
    "3dp": {
        "name": "Drug Development Data Platform (3DP)",
        "description": (
            "Central platform for managing Chemistry, Manufacturing, and Controls "
            "(CMC) data used in CTD Module 2 and Module 3 regulatory submissions. "
            "Houses batch records, stability studies, analytical methods, and "
            "specification limits required by FDA, EMA, and PMDA filings."
        ),
        "depth": "deep",
        "tech_stack": ["Python", "PostgreSQL", "Apache Airflow", "AWS S3", "Pandas"],
        "test_domains": [
            "CTD Module 3 field validation",
            "Batch formula consistency checks",
            "Stability data integrity",
            "Specification limit enforcement",
            "Cross-module referential integrity",
            "Container closure system traceability",
        ],
        "data_dir": "backend/data/platforms/3dp",
        "icon": "flask",
        "color": "#3b82f6",
        "sample_queries": [
            "Generate test cases for CTD Module 3 substance characterisation fields",
            "Validate batch formula records against approved specification limits",
            "Check stability data completeness for 36-month long-term studies",
        ],
        "metrics": {
            "total_tests": 1_247,
            "pass_rate": 94.6,
            "avg_execution_time": 3.2,
            "manual_equivalent": 104,
        },
    },
    "bikg": {
        "name": "Biological Intelligence Knowledge Graph (BIKG)",
        "description": (
            "Enterprise knowledge graph that encodes biological relationships "
            "between genes, proteins, diseases, compounds, and pathways. "
            "Supports target identification, mechanism-of-action elucidation, "
            "and drug-repurposing analyses via SPARQL and Cypher queries."
        ),
        "depth": "deep",
        "tech_stack": ["Neo4j", "SPARQL", "Python", "RDF/OWL", "NetworkX"],
        "test_domains": [
            "Knowledge graph query correctness",
            "Ontology alignment validation",
            "Relationship cardinality checks",
            "Evidence score thresholds",
            "Cross-species ortholog mapping",
            "Publication reference integrity",
        ],
        "data_dir": "backend/data/platforms/bikg",
        "icon": "brain",
        "color": "#8b5cf6",
        "sample_queries": [
            "Validate gene-disease relationship edges for oncology targets",
            "Test ontology term resolution across MeSH, GO, and HPO vocabularies",
            "Check evidence score distributions for protein-protein interactions",
        ],
        "metrics": {
            "total_tests": 983,
            "pass_rate": 97.1,
            "avg_execution_time": 2.8,
            "manual_equivalent": 88,
        },
    },
    "patient_safety": {
        "name": "Pharmacovigilance & Patient Safety System",
        "description": (
            "GxP-regulated system for capturing, processing, and submitting "
            "Individual Case Safety Reports (ICSRs). Enforces MedDRA coding, "
            "E2B(R3) XML generation, and expedited/periodic reporting timelines "
            "mandated by ICH, FDA, and EMA pharmacovigilance regulations."
        ),
        "depth": "deep",
        "tech_stack": ["Java", "Oracle DB", "MedDRA", "E2B(R3) XML", "AWS Lambda"],
        "test_domains": [
            "ICSR field-level validation",
            "MedDRA coding accuracy",
            "E2B(R3) XML schema compliance",
            "Expedited reporting timeline enforcement",
            "Signal detection data integrity",
            "Causality assessment logic",
        ],
        "data_dir": "backend/data/platforms/patient_safety",
        "icon": "shield",
        "color": "#ef4444",
        "sample_queries": [
            "Generate ICSR validation tests for serious adverse event submissions",
            "Validate MedDRA LLT-to-PT coding against version 26.1 hierarchy",
            "Test E2B(R3) XML output compliance for FDA VAERS gateway submission",
        ],
        "metrics": {
            "total_tests": 1_562,
            "pass_rate": 92.3,
            "avg_execution_time": 4.1,
            "manual_equivalent": 120,
        },
    },
    "clinical_trials": {
        "name": "CDISC / SDTM Clinical Trials Platform",
        "description": (
            "Platform for managing clinical trial data in CDISC-compliant "
            "formats including SDTM (Study Data Tabulation Model) and ADaM "
            "(Analysis Data Model). Supports define.xml generation, Pinnacle 21 "
            "validation, and FDA eSubmission gateway readiness."
        ),
        "depth": "deep",
        "tech_stack": ["SAS", "R", "Python", "CDISC Library API", "Pinnacle 21"],
        "test_domains": [
            "SDTM domain structure validation",
            "ADaM dataset derivation checks",
            "Define.xml metadata consistency",
            "Controlled terminology compliance",
            "Variable-level conformance rules",
            "Cross-domain referential integrity",
        ],
        "data_dir": "backend/data/platforms/clinical_trials",
        "icon": "microscope",
        "color": "#10b981",
        "sample_queries": [
            "Generate SDTM domain conformance tests for DM, AE, and LB datasets",
            "Validate ADaM ADSL derivation rules against analysis results metadata",
            "Check controlled terminology alignment with CDISC CT 2024-03-29 package",
        ],
        "metrics": {
            "total_tests": 2_104,
            "pass_rate": 91.8,
            "avg_execution_time": 5.6,
            "manual_equivalent": 160,
        },
    },

    # =========================================================================
    # VISUAL PLATFORMS  (dashboard metrics & monitoring only)
    # =========================================================================
    "cdisc_adam": {
        "name": "CDISC ADaM Analytics",
        "description": (
            "Monitoring dashboard for ADaM (Analysis Data Model) dataset "
            "generation pipelines. Tracks derivation rule coverage, traceability "
            "to SDTM sources, and analysis-readiness across therapeutic areas."
        ),
        "depth": "visual",
        "icon": "table",
        "color": "#f59e0b",
        "metrics": {
            "total_tests": 876,
            "pass_rate": 93.4,
            "avg_execution_time": 3.9,
            "manual_equivalent": 72,
        },
    },
    "regulatory_docs": {
        "name": "Regulatory Document Management",
        "description": (
            "Visual monitoring of the regulatory document lifecycle including "
            "eCTD assembly, submission-ready PDF validation, and cross-reference "
            "integrity checks across Module 1 through Module 5 documents."
        ),
        "depth": "visual",
        "icon": "file-text",
        "color": "#6366f1",
        "metrics": {
            "total_tests": 654,
            "pass_rate": 96.2,
            "avg_execution_time": 2.1,
            "manual_equivalent": 56,
        },
    },
    "study_pldb": {
        "name": "Study Protocol & Design Database",
        "description": (
            "Dashboard for monitoring test coverage of the study protocol "
            "lifecycle database, including protocol amendments, eligibility "
            "criteria validation, and endpoint definition consistency."
        ),
        "depth": "visual",
        "icon": "database",
        "color": "#ec4899",
        "metrics": {
            "total_tests": 512,
            "pass_rate": 95.7,
            "avg_execution_time": 1.8,
            "manual_equivalent": 48,
        },
    },
    "gxp_systems": {
        "name": "GxP Validated Systems",
        "description": (
            "Compliance monitoring for GxP-validated infrastructure including "
            "computer system validation (CSV) status, 21 CFR Part 11 controls, "
            "audit trail integrity, and electronic signature enforcement."
        ),
        "depth": "visual",
        "icon": "lock",
        "color": "#14b8a6",
        "metrics": {
            "total_tests": 738,
            "pass_rate": 98.1,
            "avg_execution_time": 2.4,
            "manual_equivalent": 64,
        },
    },
    "hpc_environment": {
        "name": "HPC - High Performance Computing Environment",
        "description": (
            "R&D high-performance computing infrastructure used for genomics "
            "pipelines, molecular dynamics simulations, PKPD modelling, and "
            "population PK analyses. Requires validation of job scheduling "
            "fairness, resource allocation correctness, computational "
            "reproducibility across nodes, metadata-scenario consistency, "
            "and SLURM/PBS configuration integrity."
        ),
        "depth": "deep",
        "tech_stack": ["Python", "Bash/SLURM", "Singularity", "Nextflow", "R"],
        "test_domains": [
            "Job scheduling and queue priority validation",
            "Resource allocation fairness checks",
            "Computational reproducibility verification",
            "Metadata-scenario consistency testing",
            "Container image integrity validation",
            "Parallel execution correctness",
        ],
        "data_dir": "backend/data/platforms/hpc_environment",
        "icon": "cpu",
        "color": "#f97316",
        "sample_queries": [
            "Validate HPC job scheduling fairness across genomics workloads",
            "Test computational reproducibility for PKPD modelling pipelines",
            "Check metadata-scenario consistency for population PK batch runs",
        ],
        "metrics": {
            "total_tests": 423,
            "pass_rate": 97.5,
            "avg_execution_time": 1.5,
            "manual_equivalent": 40,
        },
    },
}


def get_platform(platform_id: str) -> dict | None:
    """Return a single platform definition by ID, or None if not found."""
    return PLATFORM_CATALOGUE.get(platform_id)


def get_deep_platforms() -> dict:
    """Return only the deep platforms that support full test generation."""
    return {
        pid: pdata
        for pid, pdata in PLATFORM_CATALOGUE.items()
        if pdata["depth"] == "deep"
    }


def get_visual_platforms() -> dict:
    """Return only the visual/dashboard-level platforms."""
    return {
        pid: pdata
        for pid, pdata in PLATFORM_CATALOGUE.items()
        if pdata["depth"] == "visual"
    }


def list_platform_ids() -> list[str]:
    """Return a sorted list of all platform IDs."""
    return sorted(PLATFORM_CATALOGUE.keys())
