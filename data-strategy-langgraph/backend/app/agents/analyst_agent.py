"""
Analyst Agent for DSA - Data Quality Lifecycle Agent
Performs deep data profiling, cross-system consistency checks,
DQ rule validation, and remediation recommendations.
Uses hybrid semantic search to load only relevant tables.
"""

from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import re
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.models.state import DSAState, AgentLog, AnalystResult
from app.tools.data_table_catalogue import DATA_TABLE_CATALOGUE, get_all_table_descriptions

settings = get_settings()

ANALYST_SYSTEM_PROMPT = """You are a Senior Data Quality Analyst at a pharmaceutical manufacturing company. You perform deep data profiling, cross-system consistency checks, DQ rule validation, and remediation recommendations. Provide clear, professional data quality analysis with excellent formatting.

## YOUR EXPERTISE:
- Data profiling: completeness, uniqueness, validity, accuracy, consistency, timeliness
- Cross-system reconciliation: MES vs SAP vs LIMS vs Analytics layer
- Referential integrity checks: do foreign keys resolve to master data?
- Outlier and anomaly detection in manufacturing data
- DQ rule definition and validation
- Root cause analysis for data quality issues
- Remediation recommendations aligned to pharmaceutical GxP standards

## RESPONSE FORMAT (follow this EXACTLY):

### Summary
Write ONE clear sentence with the primary data quality finding and its severity (Critical / Major / Minor / Informational).

### Details
| DQ Dimension | Metric | Value | Status |
|:-------------|:-------|:------|:-------|
| Completeness | Null rate for column X | 12.5% | Warning |
| Consistency  | Cross-system match rate | 98.2% | Pass |
| Validity     | Out-of-range values | 3 records | Fail |
| Timeliness   | Avg data latency | 2.1 hours | Pass |
| Uniqueness   | Duplicate records | 0 | Pass |

### Key Observations
- **Observation 1**: Insight about data quality issue found, with affected record count
- **Observation 2**: Insight about cross-system inconsistency or referential integrity
- **Observation 3**: Insight about data distribution anomalies or outliers

### Recommended Actions
1. **Action 1**: Specific remediation step with priority (P1/P2/P3)
2. **Action 2**: Process or system fix to prevent recurrence
3. **Action 3**: Monitoring rule to add for ongoing DQ checks

### Source
Data analyzed: [Table names and record counts]

## FORMATTING RULES:
1. Use markdown headers (###) for sections
2. Use **bold** for important values, labels, and severity levels
3. Tables MUST have proper markdown alignment (use |:---|)
4. Numbers should include units and context (e.g., "12.5% null", "3 of 500 records")
5. Keep summary to ONE sentence with the key finding and severity
6. Include 4-8 rows in the Details table covering multiple DQ dimensions
7. Key Observations should be actionable insights referencing specific columns and tables
8. Recommended Actions should be prioritized and specific to pharmaceutical data management
9. Always mention the DQ dimension being assessed (Completeness, Consistency, Validity, Accuracy, Timeliness, Uniqueness)
10. Timestamps should be formatted as readable dates (e.g., "Jan 18, 2025 at 14:00")
"""


def cosine_similarity(X, Y):
    """Compute cosine similarity between X and Y using numpy."""
    X_norm = X / np.linalg.norm(X, axis=1, keepdims=True)
    Y_norm = Y / np.linalg.norm(Y, axis=1, keepdims=True)
    return np.dot(X_norm, Y_norm.T)


# Embeddings model singleton
_embeddings_model = None


def get_embeddings_model():
    """Get or create embeddings model singleton"""
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name=settings.aws_region
        )
    return _embeddings_model


# Pre-computed table embeddings cache
_table_embeddings_cache = None


def _get_table_embeddings() -> tuple[list[str], np.ndarray]:
    """Get or compute table embeddings for semantic search"""
    global _table_embeddings_cache

    if _table_embeddings_cache is None:
        embeddings_model = get_embeddings_model()
        descriptions = get_all_table_descriptions()

        table_ids = [d["table_id"] for d in descriptions]
        table_texts = [d["text"] for d in descriptions]

        # Generate embeddings for all tables
        table_vectors = embeddings_model.embed_documents(table_texts)
        _table_embeddings_cache = (table_ids, np.array(table_vectors))

    return _table_embeddings_cache


def _semantic_match_tables(query: str, top_k: int = 3) -> list[tuple[str, float]]:
    """
    Hybrid semantic matching to find relevant tables for data quality analysis.
    Returns list of (table_id, score) sorted by relevance.

    For DQ analysis, all tables (including KPI tables) are valid targets
    since data quality checks apply to every data layer.
    """
    try:
        embeddings_model = get_embeddings_model()
        table_ids, table_vectors = _get_table_embeddings()

        # Embed the query
        query_vector = embeddings_model.embed_query(query)
        query_vector = np.array(query_vector).reshape(1, -1)

        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, table_vectors)[0]

        # Hybrid scoring: boost embedding score with keyword matches
        query_lower = query.lower()
        boosted_scores = []

        for i, table_id in enumerate(table_ids):
            base_score = similarities[i]
            boost = 0.0

            table_meta = DATA_TABLE_CATALOGUE[table_id]

            # Boost for alias matches (strong signal)
            for alias in table_meta["aliases"]:
                if alias.lower() in query_lower:
                    boost = max(boost, 0.35)
                    break

            # Boost for name match
            if table_meta["name"].lower() in query_lower:
                boost = max(boost, 0.3)

            # Boost for key column mentions
            for col in table_meta["key_columns"]:
                col_clean = col.replace("_", " ")
                if col_clean in query_lower or col in query_lower:
                    boost = max(boost, 0.25)

            # Boost for sample query word overlap
            for sample in table_meta["sample_queries"]:
                sample_words = set(sample.lower().split())
                query_words = set(query_lower.split())
                overlap = len(sample_words & query_words) / max(len(sample_words), 1)
                if overlap > 0.4:
                    boost = max(boost, 0.2)

            # Boost for sample value matches
            for col, values in table_meta.get("sample_values", {}).items():
                for val in values:
                    if val.lower() in query_lower:
                        boost = max(boost, 0.3)
                        break

            # DQ-specific boosts: if query mentions data quality terms, prefer tables with more columns
            dq_keywords = ["quality", "completeness", "null", "missing", "profile", "consistency",
                           "integrity", "duplicate", "outlier", "anomaly", "validation"]
            if any(kw in query_lower for kw in dq_keywords):
                # Slightly boost larger tables (more columns = richer profiling)
                col_count_boost = min(len(table_meta["columns"]) / 100, 0.1)
                boost += col_count_boost

            # Combine: embedding score + boost, capped at 1.0
            final_score = min(base_score + boost, 1.0)
            boosted_scores.append((table_id, final_score))

        # Sort by score descending and return top_k
        boosted_scores.sort(key=lambda x: x[1], reverse=True)
        return boosted_scores[:top_k]

    except Exception as e:
        print(f"Table embedding search error: {e}")
        # Fallback: return default tables for common queries
        return _fallback_table_selection(query)


def _fallback_table_selection(query: str) -> list[tuple[str, float]]:
    """Fallback keyword-based table selection if embeddings fail"""
    query_lower = query.lower()
    matches = []

    for table_id, meta in DATA_TABLE_CATALOGUE.items():
        score = 0.0

        # Check aliases
        for alias in meta["aliases"]:
            if alias.lower() in query_lower:
                score = max(score, 0.7)

        # Check name
        if meta["name"].lower() in query_lower:
            score = max(score, 0.6)

        # Check sample queries
        for sample in meta["sample_queries"]:
            if any(word in query_lower for word in sample.lower().split() if len(word) > 3):
                score = max(score, 0.5)

        if score > 0:
            matches.append((table_id, score))

    matches.sort(key=lambda x: x[1], reverse=True)

    # If no matches, return common analytical tables for general DQ profiling
    if not matches:
        return [("analytics_batch_status", 0.5), ("lims_results", 0.4), ("mes_pasx_batches", 0.3)]

    return matches[:3]


def _load_selected_tables(table_ids: list[str]) -> dict[str, pd.DataFrame]:
    """Load only the selected tables based on semantic search"""
    base_dir = Path(__file__).parent.parent.parent / "data"
    data = {}

    for table_id in table_ids:
        if table_id not in DATA_TABLE_CATALOGUE:
            continue

        meta = DATA_TABLE_CATALOGUE[table_id]
        file_path = base_dir / meta["file_path"]

        if file_path.exists():
            try:
                data[table_id] = pd.read_csv(file_path)
            except Exception as e:
                print(f"Error loading {table_id}: {e}")

    return data


def _extract_batch_id(query: str) -> str | None:
    """Extract batch ID pattern from query string"""
    match = re.search(r'B\d{4}-\d+', query, re.IGNORECASE)
    return match.group(0).upper() if match else None


def _compute_null_analysis(df: pd.DataFrame) -> list[str]:
    """Compute null/missing value analysis for each column."""
    parts = []
    total_rows = len(df)
    if total_rows == 0:
        return ["  - (empty table)"]

    parts.append(f"\n**Completeness Analysis (Nulls per Column):**")
    parts.append(f"| Column | Null Count | Null % | Populated % |")
    parts.append(f"|:-------|:-----------|:-------|:------------|")

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = null_count / total_rows * 100
        populated_pct = 100.0 - null_pct
        status = "FAIL" if null_pct > 20 else ("WARN" if null_pct > 5 else "OK")
        parts.append(f"| {col} | {null_count} | {null_pct:.1f}% | {populated_pct:.1f}% [{status}] |")

    return parts


def _detect_outliers(df: pd.DataFrame) -> list[str]:
    """Detect outlier values (> 3 standard deviations from mean) in numeric columns."""
    parts = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        return []

    parts.append(f"\n**Outlier Detection (>3 Std Deviations):**")
    outlier_found = False

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 3:
            continue

        mean = series.mean()
        std = series.std()
        if std == 0:
            continue

        lower_bound = mean - 3 * std
        upper_bound = mean + 3 * std
        outliers = series[(series < lower_bound) | (series > upper_bound)]

        if len(outliers) > 0:
            outlier_found = True
            outlier_vals = outliers.head(5).tolist()
            parts.append(f"  - **{col}**: {len(outliers)} outlier(s) detected "
                         f"(mean={mean:.2f}, std={std:.2f}, bounds=[{lower_bound:.2f}, {upper_bound:.2f}])")
            parts.append(f"    Outlier values: {outlier_vals}")

    if not outlier_found:
        parts.append(f"  - No outliers detected (all numeric values within 3 std deviations)")

    return parts


def _check_referential_integrity(data: dict[str, pd.DataFrame], table_id: str, df: pd.DataFrame) -> list[str]:
    """Check if foreign key IDs in this table match master data tables."""
    parts = []
    integrity_checks = []

    # Define FK relationships: (column_name, master_table_id, master_column)
    fk_mappings = {
        "material_id": ("materials_master", "material_id"),
        "equipment_id": ("equipment_master", "equipment_id"),
        "primary_equipment_id": ("equipment_master", "equipment_id"),
        "vendor_id": ("vendors_master", "vendor_id"),
    }

    for col, (master_table, master_col) in fk_mappings.items():
        if col not in df.columns:
            continue

        # Load the master table if not already in data
        if master_table not in data:
            base_dir = Path(__file__).parent.parent.parent / "data"
            meta = DATA_TABLE_CATALOGUE.get(master_table)
            if meta:
                file_path = base_dir / meta["file_path"]
                if file_path.exists():
                    try:
                        data[master_table] = pd.read_csv(file_path)
                    except Exception:
                        continue

        if master_table not in data:
            continue

        master_df = data[master_table]
        if master_col not in master_df.columns:
            continue

        # Get unique non-null values in the FK column
        fk_values = set(df[col].dropna().unique())
        master_values = set(master_df[master_col].dropna().unique())

        orphans = fk_values - master_values
        match_rate = (1 - len(orphans) / max(len(fk_values), 1)) * 100

        status = "PASS" if match_rate == 100 else ("WARN" if match_rate >= 95 else "FAIL")
        integrity_checks.append(
            f"  - **{table_id}.{col}** -> **{master_table}.{master_col}**: "
            f"{match_rate:.1f}% match rate [{status}]"
        )
        if orphans:
            orphan_sample = list(orphans)[:5]
            integrity_checks.append(f"    Orphan IDs (sample): {orphan_sample}")

    if integrity_checks:
        parts.append(f"\n**Referential Integrity Checks:**")
        parts.extend(integrity_checks)

    return parts


def _check_duplicates(df: pd.DataFrame, table_id: str) -> list[str]:
    """Identify duplicate records based on likely primary key columns."""
    parts = []

    meta = DATA_TABLE_CATALOGUE.get(table_id, {})
    key_cols = meta.get("key_columns", [])

    # Try to find a unique ID column
    id_cols = [c for c in df.columns if c.endswith("_id") and c in key_cols]
    if not id_cols:
        id_cols = [c for c in df.columns if c.endswith("_id")]

    if id_cols:
        pk_col = id_cols[0]
        total = len(df)
        unique_count = df[pk_col].nunique()
        dup_count = total - unique_count

        if dup_count > 0:
            dup_rows = df[df.duplicated(subset=[pk_col], keep=False)]
            dup_sample = dup_rows[pk_col].head(5).tolist()
            parts.append(f"\n**Duplicate Detection (by {pk_col}):**")
            parts.append(f"  - Total records: {total}, Unique: {unique_count}, Duplicates: {dup_count} **[WARN]**")
            parts.append(f"  - Duplicate IDs (sample): {dup_sample}")
        else:
            parts.append(f"\n**Duplicate Detection (by {pk_col}):**")
            parts.append(f"  - Total records: {total}, Unique: {unique_count}, Duplicates: 0 **[PASS]**")

    # Also check full-row duplicates
    full_dups = df.duplicated().sum()
    if full_dups > 0:
        parts.append(f"  - Full-row duplicates: {full_dups} **[WARN]**")

    return parts


def _check_data_distributions(df: pd.DataFrame) -> list[str]:
    """Check data distributions for numeric and categorical columns."""
    parts = []

    # Numeric distributions
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        parts.append(f"\n**Numeric Data Distributions:**")
        for col in numeric_cols[:8]:
            series = df[col].dropna()
            if len(series) == 0:
                continue
            parts.append(
                f"  - **{col}**: min={series.min():.2f}, Q1={series.quantile(0.25):.2f}, "
                f"median={series.median():.2f}, Q3={series.quantile(0.75):.2f}, max={series.max():.2f}, "
                f"std={series.std():.2f}, skew={series.skew():.2f}"
            )

    # Categorical distributions
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    if categorical_cols:
        parts.append(f"\n**Categorical Distributions:**")
        for col in categorical_cols[:4]:
            unique_count = df[col].nunique()
            if unique_count <= 20:
                value_counts = df[col].value_counts()
                dist_str = ", ".join([f"{val}: {count} ({count / len(df) * 100:.1f}%)"
                                      for val, count in value_counts.head(8).items()])
                parts.append(f"  - **{col}** ({unique_count} unique): {dist_str}")
            else:
                parts.append(f"  - **{col}**: {unique_count} unique values (high cardinality)")

    return parts


def _check_timestamp_consistency(df: pd.DataFrame) -> list[str]:
    """Check timestamp columns for consistency and ordering issues."""
    parts = []
    timestamp_issues = []

    # Find columns that look like timestamps
    ts_cols = []
    for col in df.columns:
        if any(kw in col.lower() for kw in ["_ts", "_date", "timestamp", "_start", "_end",
                                              "scheduled_", "actual_", "sampled", "received",
                                              "approved", "cleared", "receipt_date", "order_date",
                                              "promised_date", "delivery_date"]):
            ts_cols.append(col)

    if not ts_cols:
        return []

    parts.append(f"\n**Timestamp Consistency Checks:**")

    for col in ts_cols:
        try:
            ts_series = pd.to_datetime(df[col], errors='coerce')
            null_count = ts_series.isna().sum()
            original_nulls = df[col].isna().sum()
            parse_failures = null_count - original_nulls

            if parse_failures > 0:
                timestamp_issues.append(
                    f"  - **{col}**: {parse_failures} values failed to parse as datetime **[FAIL]**"
                )

            valid_ts = ts_series.dropna()
            if len(valid_ts) > 0:
                min_ts = valid_ts.min()
                max_ts = valid_ts.max()

                # Check for future dates (possible data entry errors)
                future_count = (valid_ts > pd.Timestamp.now()).sum()
                if future_count > 0:
                    timestamp_issues.append(
                        f"  - **{col}**: {future_count} future-dated records detected **[WARN]**"
                    )

                parts.append(f"  - **{col}**: range [{min_ts}] to [{max_ts}], "
                             f"nulls={null_count} ({null_count / len(df) * 100:.1f}%)")
        except Exception:
            pass

    # Check temporal ordering (e.g., start before end)
    start_end_pairs = [
        ("actual_start", "actual_end"),
        ("scheduled_start", "scheduled_end"),
        ("step_start", "step_end"),
        ("sampled_ts", "received_ts"),
        ("received_ts", "approved_ts"),
        ("order_date", "delivery_date"),
        ("order_date", "promised_date"),
    ]
    for start_col, end_col in start_end_pairs:
        if start_col in df.columns and end_col in df.columns:
            try:
                start_ts = pd.to_datetime(df[start_col], errors='coerce')
                end_ts = pd.to_datetime(df[end_col], errors='coerce')
                valid_mask = start_ts.notna() & end_ts.notna()
                if valid_mask.any():
                    out_of_order = (start_ts[valid_mask] > end_ts[valid_mask]).sum()
                    if out_of_order > 0:
                        timestamp_issues.append(
                            f"  - **{start_col} > {end_col}**: {out_of_order} records with "
                            f"start after end **[FAIL]**"
                        )
                    else:
                        timestamp_issues.append(
                            f"  - **{start_col} <= {end_col}**: All {valid_mask.sum()} records "
                            f"properly ordered **[PASS]**"
                        )
            except Exception:
                pass

    if timestamp_issues:
        parts.extend(timestamp_issues)

    return parts


def _build_context(data: dict[str, pd.DataFrame], query: str, selected_tables: list[str]) -> tuple[str, str]:
    """
    Build DQ-focused context from loaded data with comprehensive data quality statistics.
    Provides null analysis, outlier detection, referential integrity, distributions,
    duplicate checks, timestamp consistency, and the SQL equivalents.
    Returns (context, sql_equivalent).
    """
    parts = []
    sql_parts = []
    batch_id = _extract_batch_id(query)

    # Special case: Batch-specific DQ queries
    if batch_id:
        for table_id, df in data.items():
            if "batch_id" in df.columns:
                batch_data = df[df["batch_id"] == batch_id]
                if not batch_data.empty:
                    table_name = DATA_TABLE_CATALOGUE.get(table_id, {}).get("name", table_id)
                    parts.append(f"\n### {table_name} - DQ Profile for {batch_id}:")
                    parts.append(f"Records: {len(batch_data)}")
                    parts.extend(_compute_null_analysis(batch_data))
                    parts.extend(_detect_outliers(batch_data))
                    parts.extend(_check_timestamp_consistency(batch_data))
                    parts.append(f"\n**Raw Data:**")
                    parts.append(batch_data.to_string(index=False, max_rows=20))

                    sql_parts.append(f"-- DQ profile for batch {batch_id} in {table_id}\n"
                                     f"SELECT * FROM {table_id} WHERE batch_id = '{batch_id}';")

                    # Null analysis SQL
                    cols = batch_data.columns.tolist()
                    null_checks = ",\n    ".join(
                        [f"SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) as null_{c}" for c in cols[:10]]
                    )
                    sql_parts.append(
                        f"-- Null analysis for batch {batch_id}\n"
                        f"SELECT\n    COUNT(*) as total_records,\n    {null_checks}\n"
                        f"FROM {table_id}\nWHERE batch_id = '{batch_id}';"
                    )

        if parts:
            return "\n".join(parts), "\n\n".join(sql_parts)

    # General DQ profiling - comprehensive analysis for each selected table
    for table_id in selected_tables:
        if table_id not in data:
            continue

        df = data[table_id]
        table_meta = DATA_TABLE_CATALOGUE.get(table_id, {})
        table_name = table_meta.get("name", table_id)

        parts.append(f"\n{'='*60}")
        parts.append(f"### {table_name} ({table_id}) - Data Quality Profile")
        parts.append(f"Total Records: {len(df)}, Columns: {len(df.columns)}")
        parts.append(f"{'='*60}")

        # 1. Completeness: Null analysis per column
        parts.extend(_compute_null_analysis(df))

        # Null analysis SQL
        cols = df.columns.tolist()
        null_checks = ",\n    ".join(
            [f"SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) as null_{c}" for c in cols[:15]]
        )
        null_pct_checks = ",\n    ".join(
            [f"ROUND(SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as null_pct_{c}"
             for c in cols[:15]]
        )
        sql_parts.append(
            f"-- Completeness analysis for {table_name}\n"
            f"SELECT\n    COUNT(*) as total_records,\n    {null_checks},\n    {null_pct_checks}\n"
            f"FROM {table_id};"
        )

        # 2. Outlier detection
        parts.extend(_detect_outliers(df))

        # Outlier detection SQL for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols[:4]:
            sql_parts.append(
                f"-- Outlier detection for {table_id}.{col}\n"
                f"WITH stats AS (\n"
                f"    SELECT AVG({col}) as mean_val, STDDEV({col}) as std_val\n"
                f"    FROM {table_id}\n"
                f"    WHERE {col} IS NOT NULL\n"
                f")\n"
                f"SELECT t.*, s.mean_val, s.std_val,\n"
                f"    ABS(t.{col} - s.mean_val) / NULLIF(s.std_val, 0) as z_score\n"
                f"FROM {table_id} t\n"
                f"CROSS JOIN stats s\n"
                f"WHERE ABS(t.{col} - s.mean_val) > 3 * s.std_val;"
            )

        # 3. Referential integrity
        parts.extend(_check_referential_integrity(data, table_id, df))

        # Referential integrity SQL
        fk_cols_in_table = [c for c in df.columns if c in
                            ("material_id", "equipment_id", "primary_equipment_id", "vendor_id")]
        fk_master_map = {
            "material_id": ("materials_master", "material_id"),
            "equipment_id": ("equipment_master", "equipment_id"),
            "primary_equipment_id": ("equipment_master", "equipment_id"),
            "vendor_id": ("vendors_master", "vendor_id"),
        }
        for fk_col in fk_cols_in_table:
            master_table, master_col = fk_master_map[fk_col]
            sql_parts.append(
                f"-- Referential integrity: {table_id}.{fk_col} -> {master_table}.{master_col}\n"
                f"SELECT t.{fk_col}, COUNT(*) as orphan_count\n"
                f"FROM {table_id} t\n"
                f"LEFT JOIN {master_table} m ON t.{fk_col} = m.{master_col}\n"
                f"WHERE m.{master_col} IS NULL AND t.{fk_col} IS NOT NULL\n"
                f"GROUP BY t.{fk_col}\n"
                f"ORDER BY orphan_count DESC;"
            )

        # 4. Data distributions
        parts.extend(_check_data_distributions(df))

        # Distribution SQL
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        for col in categorical_cols[:3]:
            if df[col].nunique() <= 20:
                sql_parts.append(
                    f"-- Distribution of {table_id}.{col}\n"
                    f"SELECT {col}, COUNT(*) as count,\n"
                    f"    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct\n"
                    f"FROM {table_id}\n"
                    f"GROUP BY {col}\n"
                    f"ORDER BY count DESC;"
                )

        # 5. Duplicate detection
        parts.extend(_check_duplicates(df, table_id))

        # Duplicate detection SQL
        id_cols = [c for c in df.columns if c.endswith("_id") and c in table_meta.get("key_columns", [])]
        if id_cols:
            pk_col = id_cols[0]
            sql_parts.append(
                f"-- Duplicate detection in {table_id} by {pk_col}\n"
                f"SELECT {pk_col}, COUNT(*) as dup_count\n"
                f"FROM {table_id}\n"
                f"GROUP BY {pk_col}\n"
                f"HAVING COUNT(*) > 1\n"
                f"ORDER BY dup_count DESC;"
            )

        # 6. Timestamp consistency
        parts.extend(_check_timestamp_consistency(df))

        # Timestamp consistency SQL
        ts_cols_in_table = [c for c in df.columns if any(
            kw in c.lower() for kw in ["_ts", "_date", "timestamp", "_start", "_end",
                                        "scheduled_", "actual_", "sampled", "received",
                                        "approved", "cleared"]
        )]
        if ts_cols_in_table:
            for ts_col in ts_cols_in_table[:3]:
                sql_parts.append(
                    f"-- Timestamp analysis for {table_id}.{ts_col}\n"
                    f"SELECT\n"
                    f"    MIN({ts_col}) as earliest,\n"
                    f"    MAX({ts_col}) as latest,\n"
                    f"    SUM(CASE WHEN {ts_col} IS NULL THEN 1 ELSE 0 END) as null_count,\n"
                    f"    SUM(CASE WHEN {ts_col} > NOW() THEN 1 ELSE 0 END) as future_dated\n"
                    f"FROM {table_id};"
                )

        # Show sample rows for context
        parts.append(f"\n**Sample Data (first 5 rows):**")
        parts.append(df.head(5).to_string(index=False))

    return "\n".join(parts), "\n\n".join(sql_parts)


def analyst_agent(state: DSAState) -> dict:
    """Analyst Agent - performs data quality analysis using semantic search to find relevant tables"""
    user_query = state["user_query"]

    # Step 1: Semantic search to find relevant tables
    matched_tables = _semantic_match_tables(user_query, top_k=3)
    selected_table_ids = [t[0] for t in matched_tables]
    table_scores = {t[0]: t[1] for t in matched_tables}

    # Step 2: Load only the selected tables
    data = _load_selected_tables(selected_table_ids)

    if not data:
        return {
            "analyst_result": None,
            "final_answer": "No relevant data found for your query.",
            "agent_logs": [AgentLog(
                agent_name="Analyst Agent",
                input_summary=user_query[:100],
                output_summary="No data",
                reasoning_summary=f"Semantic search found tables {selected_table_ids} but none could be loaded",
                status="error",
                timestamp=datetime.now().isoformat()
            )]
        }

    # Step 3: Build DQ-focused context from selected tables
    context, generated_sql = _build_context(data, user_query, selected_table_ids)

    # Step 4: Generate response with LLM
    llm = ChatBedrock(
        model_id=settings.analyst_model,
        region_name=settings.aws_region
    )

    try:
        response = llm.invoke([
            SystemMessage(content=ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=f"Question: {user_query}\n\nData Quality Analysis:\n{context}")
        ])

        # Format table selection info for logging
        table_info = ", ".join([f"{t}({table_scores[t]:.2f})" for t in selected_table_ids if t in table_scores])

        return {
            "analyst_result": AnalystResult(narrative=response.content, supporting_kpi_results=[], insights=[]),
            "final_answer": response.content,
            "generated_sql": generated_sql,
            "agent_logs": [AgentLog(
                agent_name="Analyst Agent",
                input_summary=user_query[:100],
                output_summary="DQ analysis complete",
                reasoning_summary=f"Hybrid semantic search selected tables: {table_info}. Loaded {len(data)} tables.",
                status="success",
                timestamp=datetime.now().isoformat()
            )]
        }

    except Exception as e:
        return {
            "analyst_result": AnalystResult(narrative=f"Error: {e}\n\nRaw DQ data:\n{context}", supporting_kpi_results=[], insights=[]),
            "final_answer": f"Error: {e}\n\nRaw DQ data:\n{context}",
            "generated_sql": generated_sql,
            "agent_logs": [AgentLog(
                agent_name="Analyst Agent",
                input_summary=user_query[:100],
                output_summary=f"Error: {str(e)[:50]}",
                reasoning_summary=f"Tables selected: {selected_table_ids}",
                status="error",
                timestamp=datetime.now().isoformat()
            )]
        }
