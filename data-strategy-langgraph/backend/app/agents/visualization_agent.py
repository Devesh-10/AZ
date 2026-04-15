"""
Visualization Agent for DSA
Generates chart configurations from DQ metric results.
"""

from datetime import datetime

from app.models.state import DSAState, AgentLog


def visualization_agent(state: DSAState) -> dict:
    kpi_results = state.get("kpi_results")
    analyst_result = state.get("analyst_result")
    existing_viz = state.get("visualization_config")

    if existing_viz:
        return {
            "agent_logs": [AgentLog(
                agent_name="Visualization",
                input_summary=f"Chart config exists",
                output_summary=f"Using existing visualization",
                reasoning_summary=f"KPI agent provided chart config, passing through",
                status="success",
                timestamp=datetime.now().isoformat()
            )]
        }

    if kpi_results and len(kpi_results) > 0:
        kpi_result = kpi_results[0]
        data_points = kpi_result.get("data_points", [])
        kpi_name = kpi_result.get("kpi_name", "DQ Metric")

        if len(data_points) > 0:
            chart_type = "bar" if len(data_points) <= 6 else "line"
            series_data = []
            for dp in data_points:
                x_val = dp.get("period", dp.get("sku", "Unknown"))
                y_val = dp.get("value", 0)
                if y_val is not None:
                    series_data.append({"x": x_val, "y": float(y_val)})

            if series_data:
                viz_config = {
                    "chartType": chart_type,
                    "title": kpi_name,
                    "xLabel": "Category",
                    "yLabel": kpi_result.get("unit", "%"),
                    "series": [{"name": kpi_name, "data": series_data}]
                }

                return {
                    "visualization_config": viz_config,
                    "agent_logs": [AgentLog(
                        agent_name="Visualization",
                        input_summary=f"DQ Metric: {kpi_name}, {len(data_points)} points",
                        output_summary=f"Generated {chart_type} chart",
                        reasoning_summary=f"Created {chart_type} visualization with {len(series_data)} data points",
                        status="success",
                        timestamp=datetime.now().isoformat()
                    )]
                }

    if analyst_result:
        return {
            "agent_logs": [AgentLog(
                agent_name="Visualization",
                input_summary="Analyst result",
                output_summary="No chart (analyst uses formatted tables)",
                reasoning_summary="Analyst queries display as formatted text/tables, no chart needed",
                status="success",
                timestamp=datetime.now().isoformat()
            )]
        }

    return {
        "agent_logs": [AgentLog(
            agent_name="Visualization",
            input_summary="No chartable data",
            output_summary="No visualization generated",
            reasoning_summary="Insufficient data for chart generation",
            status="success",
            timestamp=datetime.now().isoformat()
        )]
    }
