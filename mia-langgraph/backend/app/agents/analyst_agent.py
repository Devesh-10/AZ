"""
Analyst Agent for MIA
Accesses: Analytical, Transactional, and Master data
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
from app.models.state import MIAState, AgentLog, AnalystResult
from app.tools.data_table_catalogue import DATA_TABLE_CATALOGUE, get_all_table_descriptions

settings = get_settings()

ANALYST_SYSTEM_PROMPT = """You are a Senior Manufacturing Analyst at a pharmaceutical company. Provide clear, professional analysis with excellent formatting.

## RESPONSE FORMAT (follow this EXACTLY):

### Summary
Write ONE clear sentence with the direct answer highlighting the key metric value.

### Details
| Parameter | Value |
|:----------|:------|
| Metric 1 | Value with units |
| Metric 2 | Value with units |
| Metric 3 | Value with units |
| Metric 4 | Value with units |

### Key Observations
- **Observation 1**: Brief insight about the data
- **Observation 2**: Brief insight about trends or status
- **Observation 3**: Recommendation or action item (if applicable)

### Source
Data source: [Table name]

## FORMATTING RULES:
1. Use markdown headers (###) for sections
2. Use **bold** for important values and labels
3. Tables MUST have proper markdown alignment (use |:---|)
4. Numbers should include units (hours, %, days, etc.)
5. Keep summary to ONE sentence with the key answer
6. Include 3-5 rows in the Details table
7. Key Observations should be actionable insights, not raw data
8. Timestamps should be formatted as readable dates (e.g., "Jan 18, 2025 at 14:00")
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
    Hybrid semantic matching to find relevant tables.
    Returns list of (table_id, score) sorted by relevance.

    IMPORTANT: Excludes KPI store tables since Analyst handles complex queries
    that need transaction-level data, not pre-aggregated KPIs.
    """
    # KPI tables are handled by KPI agent, not Analyst
    EXCLUDED_TABLES = {"kpi_store_weekly", "kpi_store_monthly"}

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
            # Skip KPI tables - Analyst uses transaction/analytical data only
            if table_id in EXCLUDED_TABLES:
                continue

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

            # Boost for sample value matches (e.g., "Quarantined", "Released")
            for col, values in table_meta.get("sample_values", {}).items():
                for val in values:
                    if val.lower() in query_lower:
                        boost = max(boost, 0.3)
                        break

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
    # KPI tables are handled by KPI agent, not Analyst
    EXCLUDED_TABLES = {"kpi_store_weekly", "kpi_store_monthly"}

    query_lower = query.lower()
    matches = []

    for table_id, meta in DATA_TABLE_CATALOGUE.items():
        # Skip KPI tables
        if table_id in EXCLUDED_TABLES:
            continue

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

    # If no matches, return common analytical tables
    if not matches:
        return [("analytics_batch_status", 0.5), ("analytics_order_status", 0.4)]

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
    match = re.search(r'B\d{4}-\d+', query, re.IGNORECASE)
    return match.group(0).upper() if match else None


def _build_context(data: dict[str, pd.DataFrame], query: str, selected_tables: list[str]) -> tuple[str, str]:
    """
    Build context from loaded data with pre-computed aggregations.
    Provides summary statistics AND the SQL that would produce them.
    Returns (context, sql_equivalent).
    """
    parts = []
    sql_parts = []
    batch_id = _extract_batch_id(query)
    query_lower = query.lower()

    # Special case: Batch-specific queries need filtered data with calculations
    if batch_id:
        for table_id, df in data.items():
            if "batch_id" in df.columns:
                batch_data = df[df["batch_id"] == batch_id]
                if not batch_data.empty:
                    table_name = DATA_TABLE_CATALOGUE.get(table_id, {}).get("name", table_id)
                    parts.append(f"\n### {table_name} (filtered for {batch_id}):")
                    parts.append(batch_data.to_string(index=False, max_rows=20))
                    sql_parts.append(f"SELECT * FROM {table_id} WHERE batch_id = '{batch_id}';")

                    # For batch steps, add wait time calculation SQL
                    if table_id == "mes_pasx_batch_steps":
                        # Add SQL for calculating wait time between steps
                        sql_parts.append(f"""-- Calculate wait time between formulation (Filter) and packaging (Fill/Pack)
SELECT
    flt.batch_id,
    flt.step_name as formulation_step,
    flt.step_end as formulation_end_time,
    fill.step_name as packaging_step,
    fill.step_start as packaging_start_time,
    TIMESTAMPDIFF(MINUTE, flt.step_end, fill.step_start) as wait_time_minutes
FROM mes_pasx_batch_steps flt
JOIN mes_pasx_batch_steps fill
    ON flt.batch_id = fill.batch_id
WHERE flt.batch_id = '{batch_id}'
    AND flt.step_code IN ('FLT', 'FILTER', 'FORM')
    AND fill.step_code IN ('FILL', 'PACK', 'FP');""")

                        # Add step duration analysis SQL
                        sql_parts.append(f"""-- Step-by-step timing for batch {batch_id}
SELECT
    step_name,
    step_code,
    step_start,
    step_end,
    TIMESTAMPDIFF(MINUTE, step_start, step_end) as step_duration_min,
    wait_before_min
FROM mes_pasx_batch_steps
WHERE batch_id = '{batch_id}'
ORDER BY sequence;""")

                    # For batch status, add performance metrics SQL
                    if table_id == "analytics_batch_status":
                        sql_parts.append(f"""-- Batch performance metrics
SELECT
    batch_id,
    yield_pct,
    cycle_time_hr,
    wait_time_min,
    active_time_min,
    rft as right_first_time,
    deviations_count,
    status
FROM analytics_batch_status
WHERE batch_id = '{batch_id}';""")

        if parts:
            return "\n".join(parts), "\n\n".join(sql_parts)

    # General queries - provide comprehensive data summary with SQL
    for table_id in selected_tables:
        if table_id not in data:
            continue

        df = data[table_id]
        table_meta = DATA_TABLE_CATALOGUE.get(table_id, {})
        table_name = table_meta.get("name", table_id)

        parts.append(f"\n### {table_name} ({table_id})")
        parts.append(f"Total Records: {len(df)}")

        # Build aggregation SQL and compute stats
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        agg_sql_cols = []

        if numeric_cols:
            parts.append("\n**Aggregated Statistics:**")
            for col in numeric_cols[:8]:  # More columns for analysis
                if df[col].notna().any():
                    mean_val = df[col].mean()
                    min_val = df[col].min()
                    max_val = df[col].max()
                    sum_val = df[col].sum()
                    parts.append(f"  - {col}: avg={mean_val:.2f}, min={min_val:.2f}, max={max_val:.2f}, total={sum_val:.2f}")
                    agg_sql_cols.append(f"AVG({col}) as avg_{col}")
                    agg_sql_cols.append(f"MIN({col}) as min_{col}")
                    agg_sql_cols.append(f"MAX({col}) as max_{col}")

        # Generate aggregation SQL
        if agg_sql_cols:
            sql_parts.append(f"-- Aggregation query for {table_name}\nSELECT\n    COUNT(*) as total_records,\n    {','.join(agg_sql_cols[:6])}\nFROM {table_id};")

        # Categorical distributions with GROUP BY SQL
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        for col in categorical_cols[:3]:
            unique_count = df[col].nunique()
            if unique_count <= 15:
                value_counts = df[col].value_counts()
                parts.append(f"\n**{col} Distribution:**")
                for val, count in value_counts.head(10).items():
                    pct = count / len(df) * 100
                    parts.append(f"  - {val}: {count} ({pct:.1f}%)")
                sql_parts.append(f"-- Distribution by {col}\nSELECT {col}, COUNT(*) as count,\n    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct\nFROM {table_id}\nGROUP BY {col}\nORDER BY count DESC;")

        # For batch-related tables, add RFT/yield analysis if columns exist
        if table_id == "analytics_batch_status":
            if "rft" in df.columns:
                rft_pass = len(df[df["rft"] == 1])
                rft_fail = len(df[df["rft"] == 0])
                rft_pct = rft_pass / len(df) * 100 if len(df) > 0 else 0
                parts.append(f"\n**RFT Analysis:**")
                parts.append(f"  - RFT Pass: {rft_pass} batches ({rft_pct:.1f}%)")
                parts.append(f"  - RFT Fail: {rft_fail} batches ({100-rft_pct:.1f}%)")
                sql_parts.append(f"""-- RFT Analysis
SELECT
    SUM(CASE WHEN rft = 1 THEN 1 ELSE 0 END) as rft_pass,
    SUM(CASE WHEN rft = 0 THEN 1 ELSE 0 END) as rft_fail,
    ROUND(SUM(CASE WHEN rft = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as rft_pct
FROM analytics_batch_status;""")

            if "status" in df.columns:
                status_counts = df["status"].value_counts()
                parts.append(f"\n**Status Breakdown:**")
                for status, count in status_counts.items():
                    parts.append(f"  - {status}: {count}")

        # For batch steps, add step-level timing analysis
        if table_id == "mes_pasx_batch_steps":
            if "step_name" in df.columns and "step_duration_min" in df.columns:
                step_stats = df.groupby("step_name")["step_duration_min"].agg(["mean", "min", "max", "count"])
                parts.append(f"\n**Step Duration Analysis:**")
                for step, row in step_stats.iterrows():
                    parts.append(f"  - {step}: avg={row['mean']:.1f}min, range={row['min']:.0f}-{row['max']:.0f}min, count={int(row['count'])}")
                sql_parts.append(f"""-- Step Duration Analysis
SELECT
    step_name,
    AVG(step_duration_min) as avg_duration,
    MIN(step_duration_min) as min_duration,
    MAX(step_duration_min) as max_duration,
    COUNT(*) as step_count
FROM mes_pasx_batch_steps
GROUP BY step_name
ORDER BY avg_duration DESC;""")

        # Show sample rows for context
        parts.append(f"\n**Sample Data (first 5 rows):**")
        parts.append(df.head(5).to_string(index=False))

    return "\n".join(parts), "\n\n".join(sql_parts)


def analyst_agent(state: MIAState) -> dict:
    """Analyst Agent - uses semantic search to load only relevant data sources"""
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

    # Step 3: Build context from selected tables
    context, generated_sql = _build_context(data, user_query, selected_table_ids)

    # Step 4: Generate response with LLM
    llm = ChatBedrock(
        model_id=settings.analyst_model,
        region_name=settings.aws_region
    )

    try:
        response = llm.invoke([
            SystemMessage(content=ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=f"Question: {user_query}\n\nData:\n{context}")
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
                output_summary="Analysis complete",
                reasoning_summary=f"Hybrid semantic search selected tables: {table_info}. Loaded {len(data)} tables.",
                status="success",
                timestamp=datetime.now().isoformat()
            )]
        }

    except Exception as e:
        return {
            "analyst_result": AnalystResult(narrative=f"Error: {e}\n\nRaw data:\n{context}", supporting_kpi_results=[], insights=[]),
            "final_answer": f"Error: {e}\n\nRaw data:\n{context}",
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
