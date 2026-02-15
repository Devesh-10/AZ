"""
Visualization Agent for Sustainability Insight Agent
Generates chart configurations from KPI/Analyst results.
"""

from datetime import datetime

from app.models.state import SIAState, AgentLog


def visualization_agent(state: SIAState) -> dict:
    """
    Visualization Agent - generates chart configuration from results.

    Args:
        state: Current SIA state with results

    Returns:
        Updated state with visualization_config
    """
    kpi_results = state.get("kpi_results")
    analyst_result = state.get("analyst_result")
    existing_viz = state.get("visualization_config")

    # If visualization already exists, pass through
    if existing_viz:
        viz_type = existing_viz.get("type", "unknown")
        return {
            "agent_logs": [{
                "agent_name": "Visualization",
                "input_summary": f"Chart config: {viz_type}",
                "output_summary": f"Using existing {viz_type} visualization",
                "reasoning_summary": "KPI agent provided chart config",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }]
        }

    # Generate visualization from KPI results
    if kpi_results and len(kpi_results) > 0:
        kpi_result = kpi_results[0]
        data_points = kpi_result.get("data_points", [])
        kpi_name = kpi_result.get("kpi_name", "KPI")

        if len(data_points) > 0:
            chart_type = "bar" if len(data_points) <= 5 else "line"

            series_data = []
            for dp in data_points:
                x_val = dp.get("period", dp.get("site", "Unknown"))
                y_val = dp.get("value", 0)
                if y_val is not None:
                    series_data.append({"x": x_val, "y": float(y_val)})

            if series_data:
                viz_config = {
                    "chartType": chart_type,
                    "title": kpi_name,
                    "xLabel": "Period",
                    "yLabel": kpi_result.get("unit", ""),
                    "series": [{
                        "name": kpi_name,
                        "data": series_data
                    }]
                }

                return {
                    "visualization_config": viz_config,
                    "agent_logs": [{
                        "agent_name": "Visualization",
                        "input_summary": f"KPI: {kpi_name}, {len(data_points)} points",
                        "output_summary": f"Generated {chart_type} chart",
                        "reasoning_summary": f"Created {chart_type} with {len(series_data)} data points",
                        "status": "success",
                        "timestamp": datetime.now().isoformat()
                    }]
                }

    # For analyst results, skip visualization
    if analyst_result:
        return {
            "agent_logs": [{
                "agent_name": "Visualization",
                "input_summary": "Analyst result",
                "output_summary": "No chart (using formatted tables)",
                "reasoning_summary": "Analyst queries display as formatted text",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }]
        }

    return {
        "agent_logs": [{
            "agent_name": "Visualization",
            "input_summary": "No chartable data",
            "output_summary": "No visualization generated",
            "reasoning_summary": "Insufficient data for chart",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }]
    }
