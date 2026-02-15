"""
Analyst Agent for Sustainability Insight Agent
Handles complex sustainability queries using semantic search and data analysis.
"""

from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import re
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.models.state import SIAState, AgentLog, AnalystResult
from app.tools.data_table_catalogue import DATA_TABLE_CATALOGUE, get_all_table_descriptions

settings = get_settings()

ANALYST_SYSTEM_PROMPT = """You are a Senior Sustainability Analyst at a global pharmaceutical company. Provide clear, professional analysis with excellent formatting.

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
4. Numbers should include units (MWh, tCO2, m³, tonnes, %, etc.)
5. Keep summary to ONE sentence with the key answer
6. Include 3-5 rows in the Details table
7. Key Observations should be actionable sustainability insights
8. Reference relevant sustainability frameworks (SBTi, GHG Protocol) when appropriate
"""


def cosine_similarity(X, Y):
    """Compute cosine similarity between X and Y using numpy."""
    X_norm = X / np.linalg.norm(X, axis=1, keepdims=True)
    Y_norm = Y / np.linalg.norm(Y, axis=1, keepdims=True)
    return np.dot(X_norm, Y_norm.T)


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


_table_embeddings_cache = None


def _get_table_embeddings() -> tuple[list[str], np.ndarray]:
    """Get or compute table embeddings for semantic search"""
    global _table_embeddings_cache

    if _table_embeddings_cache is None:
        embeddings_model = get_embeddings_model()
        descriptions = get_all_table_descriptions()

        table_ids = [d["table_id"] for d in descriptions]
        table_texts = [d["text"] for d in descriptions]

        table_vectors = embeddings_model.embed_documents(table_texts)
        _table_embeddings_cache = (table_ids, np.array(table_vectors))

    return _table_embeddings_cache


def _semantic_match_tables(query: str, top_k: int = 3) -> list[tuple[str, float]]:
    """Hybrid semantic matching to find relevant tables."""
    try:
        embeddings_model = get_embeddings_model()
        table_ids, table_vectors = _get_table_embeddings()

        query_vector = embeddings_model.embed_query(query)
        query_vector = np.array(query_vector).reshape(1, -1)

        similarities = cosine_similarity(query_vector, table_vectors)[0]

        query_lower = query.lower()
        boosted_scores = []

        for i, table_id in enumerate(table_ids):
            base_score = similarities[i]
            boost = 0.0

            table_meta = DATA_TABLE_CATALOGUE[table_id]

            for alias in table_meta["aliases"]:
                if alias.lower() in query_lower:
                    boost = max(boost, 0.35)
                    break

            if table_meta["name"].lower() in query_lower:
                boost = max(boost, 0.3)

            for col in table_meta["key_columns"]:
                col_clean = col.replace("_", " ").lower()
                if col_clean in query_lower:
                    boost = max(boost, 0.25)

            final_score = min(base_score + boost, 1.0)
            boosted_scores.append((table_id, final_score))

        boosted_scores.sort(key=lambda x: x[1], reverse=True)
        return boosted_scores[:top_k]

    except Exception as e:
        print(f"Table embedding search error: {e}")
        return _fallback_table_selection(query)


def _fallback_table_selection(query: str) -> list[tuple[str, float]]:
    """Fallback keyword-based table selection"""
    query_lower = query.lower()
    matches = []

    for table_id, meta in DATA_TABLE_CATALOGUE.items():
        score = 0.0

        for alias in meta["aliases"]:
            if alias.lower() in query_lower:
                score = max(score, 0.7)

        if meta["name"].lower() in query_lower:
            score = max(score, 0.6)

        if score > 0:
            matches.append((table_id, score))

    matches.sort(key=lambda x: x[1], reverse=True)

    if not matches:
        return [("energy_monthly_summary", 0.5), ("greenhouse_gas_emissions_monthly_summary", 0.4)]

    return matches[:3]


def _load_selected_tables(table_ids: list[str]) -> dict[str, pd.DataFrame]:
    """Load only the selected tables"""
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


def _build_context(data: dict[str, pd.DataFrame], query: str, selected_tables: list[str]) -> tuple[str, str]:
    """Build context from loaded data with aggregations."""
    parts = []
    sql_parts = []
    query_lower = query.lower()

    for table_id in selected_tables:
        if table_id not in data:
            continue

        df = data[table_id]
        table_meta = DATA_TABLE_CATALOGUE.get(table_id, {})
        table_name = table_meta.get("name", table_id)

        parts.append(f"\n### {table_name} ({table_id})")
        parts.append(f"Total Records: {len(df)}")

        # Numeric stats
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        agg_sql_cols = []

        if numeric_cols:
            parts.append("\n**Aggregated Statistics:**")
            for col in numeric_cols[:8]:
                if df[col].notna().any():
                    mean_val = df[col].mean()
                    min_val = df[col].min()
                    max_val = df[col].max()
                    sum_val = df[col].sum()
                    parts.append(f"  - {col}: avg={mean_val:.2f}, min={min_val:.2f}, max={max_val:.2f}, total={sum_val:.2f}")
                    agg_sql_cols.append(f"AVG({col}) as avg_{col}")

        if agg_sql_cols:
            sql_parts.append(f"-- Aggregation for {table_name}\nSELECT\n    COUNT(*) as total_records,\n    {', '.join(agg_sql_cols[:4])}\nFROM {table_id};")

        # Categorical distributions
        if "SHE_SITE_NAME" in df.columns:
            site_counts = df["SHE_SITE_NAME"].value_counts()
            parts.append(f"\n**Sites in data:** {', '.join(site_counts.index[:5].tolist())}")

        # Year distribution
        if "REPORTING_YEAR_NUMBER" in df.columns:
            years = df["REPORTING_YEAR_NUMBER"].unique()
            parts.append(f"**Years covered:** {sorted(years)}")

        # Sample rows
        parts.append(f"\n**Sample Data (first 5 rows):**")
        parts.append(df.head(5).to_string(index=False))

    return "\n".join(parts), "\n\n".join(sql_parts)


def analyst_agent(state: SIAState) -> dict:
    """Analyst Agent - uses semantic search to load relevant data sources"""
    user_query = state["user_query"]

    # Step 1: Semantic search for relevant tables
    matched_tables = _semantic_match_tables(user_query, top_k=3)
    selected_table_ids = [t[0] for t in matched_tables]
    table_scores = {t[0]: t[1] for t in matched_tables}

    # Step 2: Load selected tables
    data = _load_selected_tables(selected_table_ids)

    if not data:
        return {
            "analyst_result": None,
            "final_answer": "No relevant data found for your query.",
            "agent_logs": [{
                "agent_name": "Analyst Agent",
                "input_summary": user_query[:100],
                "output_summary": "No data",
                "reasoning_summary": f"Tables selected: {selected_table_ids}",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }]
        }

    # Step 3: Build context
    context, generated_sql = _build_context(data, user_query, selected_table_ids)

    # Step 4: Generate response
    llm = ChatBedrock(
        model_id=settings.analyst_model,
        region_name=settings.aws_region
    )

    try:
        response = llm.invoke([
            SystemMessage(content=ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=f"Question: {user_query}\n\nData:\n{context}")
        ])

        table_info = ", ".join([f"{t}({table_scores[t]:.2f})" for t in selected_table_ids if t in table_scores])

        return {
            "analyst_result": {"narrative": response.content, "supporting_kpi_results": [], "insights": []},
            "final_answer": response.content,
            "generated_sql": generated_sql,
            "agent_logs": [{
                "agent_name": "Analyst Agent",
                "input_summary": user_query[:100],
                "output_summary": "Analysis complete",
                "reasoning_summary": f"Semantic search selected: {table_info}. Loaded {len(data)} tables.",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }]
        }

    except Exception as e:
        return {
            "analyst_result": {"narrative": f"Error: {e}\n\nRaw data:\n{context}", "supporting_kpi_results": [], "insights": []},
            "final_answer": f"Error: {e}\n\nRaw data:\n{context}",
            "generated_sql": generated_sql,
            "agent_logs": [{
                "agent_name": "Analyst Agent",
                "input_summary": user_query[:100],
                "output_summary": f"Error: {str(e)[:50]}",
                "reasoning_summary": f"Tables selected: {selected_table_ids}",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }]
        }
