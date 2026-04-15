import pandas as pd
from pathlib import Path
from langchain_core.tools import tool

DATA_PATH = Path(__file__).parent.parent / "data" / "esg_scores.csv"


def _load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


@tool
def get_company_esg(company_name: str) -> str:
    """Look up ESG scores for a specific company by name. Use this when the user asks about a specific company's ESG performance."""
    df = _load_data()
    matches = df[df["Company"].str.contains(company_name, case=False, na=False)]
    if matches.empty:
        return f"No company found matching '{company_name}'. Available companies include: {', '.join(df['Company'].head(10).tolist())}..."
    results = []
    for _, row in matches.iterrows():
        results.append(
            f"**{row['Company']}** ({row['Sector']}, {row['Country']})\n"
            f"  - Environmental: {row['Environmental_Score']}/100\n"
            f"  - Social: {row['Social_Score']}/100\n"
            f"  - Governance: {row['Governance_Score']}/100\n"
            f"  - Total ESG: {row['Total_ESG_Score']}/100\n"
            f"  - Rating: {row['ESG_Rating']}\n"
            f"  - Carbon Emissions: {row['Carbon_Emissions_tCO2']:,.0f} tCO2\n"
            f"  - Revenue: ${row['Revenue_Billion_USD']}B"
        )
    return "\n\n".join(results)


@tool
def get_top_companies(n: int = 10, metric: str = "Total_ESG_Score") -> str:
    """Get the top N companies ranked by an ESG metric. Valid metrics: Total_ESG_Score, Environmental_Score, Social_Score, Governance_Score."""
    df = _load_data()
    valid_metrics = ["Total_ESG_Score", "Environmental_Score", "Social_Score", "Governance_Score"]
    if metric not in valid_metrics:
        metric = "Total_ESG_Score"
    top = df.nlargest(min(n, len(df)), metric)
    lines = [f"**Top {len(top)} Companies by {metric.replace('_', ' ')}:**\n"]
    for i, (_, row) in enumerate(top.iterrows(), 1):
        lines.append(f"{i}. {row['Company']} ({row['Sector']}) — {row[metric]}/100 (Rating: {row['ESG_Rating']})")
    return "\n".join(lines)


@tool
def get_bottom_companies(n: int = 10) -> str:
    """Get the bottom N companies by Total ESG Score. Use when asked about worst performers or lowest ESG scores."""
    df = _load_data()
    bottom = df.nsmallest(min(n, len(df)), "Total_ESG_Score")
    lines = [f"**Bottom {len(bottom)} Companies by Total ESG Score:**\n"]
    for i, (_, row) in enumerate(bottom.iterrows(), 1):
        lines.append(f"{i}. {row['Company']} ({row['Sector']}) — {row['Total_ESG_Score']}/100 (Rating: {row['ESG_Rating']})")
    return "\n".join(lines)


@tool
def filter_companies(sector: str = "", country: str = "", min_score: float = 0, max_score: float = 100) -> str:
    """Filter companies by sector, country, and ESG score range. Leave parameters empty to skip that filter."""
    df = _load_data()
    if sector:
        df = df[df["Sector"].str.contains(sector, case=False, na=False)]
    if country:
        df = df[df["Country"].str.contains(country, case=False, na=False)]
    df = df[(df["Total_ESG_Score"] >= min_score) & (df["Total_ESG_Score"] <= max_score)]

    if df.empty:
        return "No companies match the given filters."

    df = df.sort_values("Total_ESG_Score", ascending=False)
    lines = [f"**Found {len(df)} companies:**\n"]
    for _, row in df.iterrows():
        lines.append(f"- {row['Company']} ({row['Sector']}, {row['Country']}) — ESG: {row['Total_ESG_Score']}/100 ({row['ESG_Rating']})")
    return "\n".join(lines)


@tool
def get_sector_summary() -> str:
    """Get average ESG scores broken down by sector. Use when asked about sector performance or industry comparisons."""
    df = _load_data()
    sector_avg = (
        df.groupby("Sector")[["Environmental_Score", "Social_Score", "Governance_Score", "Total_ESG_Score"]]
        .mean()
        .round(1)
        .sort_values("Total_ESG_Score", ascending=False)
    )
    lines = ["**ESG Scores by Sector:**\n"]
    for sector, row in sector_avg.iterrows():
        lines.append(
            f"- **{sector}**: Total={row['Total_ESG_Score']} | E={row['Environmental_Score']} | S={row['Social_Score']} | G={row['Governance_Score']}"
        )
    return "\n".join(lines)


@tool
def compare_companies(company_names: str) -> str:
    """Compare ESG scores of multiple companies side by side. Pass company names separated by commas."""
    df = _load_data()
    names = [n.strip() for n in company_names.split(",")]
    results = []
    for name in names:
        matches = df[df["Company"].str.contains(name, case=False, na=False)]
        if not matches.empty:
            row = matches.iloc[0]
            results.append(
                f"**{row['Company']}** ({row['Sector']})\n"
                f"  E: {row['Environmental_Score']} | S: {row['Social_Score']} | G: {row['Governance_Score']} | Total: {row['Total_ESG_Score']} | Rating: {row['ESG_Rating']}"
            )
        else:
            results.append(f"**{name}**: Not found in database")
    return "\n\n".join(results)


ALL_TOOLS = [
    get_company_esg,
    get_top_companies,
    get_bottom_companies,
    filter_companies,
    get_sector_summary,
    compare_companies,
]
