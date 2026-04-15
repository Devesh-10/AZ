from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd
from pathlib import Path

router = APIRouter()

DATA_PATH = Path(__file__).parent.parent / "data" / "esg_scores.csv"


def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


@router.get("/summary")
def get_summary():
    df = load_data()
    top_rated = df[df["ESG_Rating"].isin(["AAA", "AA"])].shape[0]
    return {
        "total_companies": len(df),
        "avg_environmental": round(df["Environmental_Score"].mean(), 1),
        "avg_social": round(df["Social_Score"].mean(), 1),
        "avg_governance": round(df["Governance_Score"].mean(), 1),
        "avg_total_esg": round(df["Total_ESG_Score"].mean(), 1),
        "top_rated_count": int(top_rated),
        "sectors": df["Sector"].nunique(),
        "countries": df["Country"].nunique(),
    }


@router.get("/companies")
def get_companies(
    sector: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    rating: Optional[str] = Query(None),
    sort_by: str = Query("Total_ESG_Score"),
    order: str = Query("desc"),
    search: Optional[str] = Query(None),
):
    df = load_data()

    if sector:
        df = df[df["Sector"] == sector]
    if country:
        df = df[df["Country"] == country]
    if rating:
        df = df[df["ESG_Rating"] == rating]
    if search:
        df = df[df["Company"].str.contains(search, case=False, na=False)]

    ascending = order == "asc"
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)

    return df.to_dict(orient="records")


@router.get("/sectors")
def get_sector_summary():
    df = load_data()
    sector_avg = (
        df.groupby("Sector")[
            ["Environmental_Score", "Social_Score", "Governance_Score", "Total_ESG_Score"]
        ]
        .mean()
        .round(1)
        .reset_index()
    )
    return sector_avg.to_dict(orient="records")


@router.get("/ratings")
def get_rating_distribution():
    df = load_data()
    rating_order = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
    counts = df["ESG_Rating"].value_counts().reindex(rating_order, fill_value=0)
    return [{"rating": r, "count": int(c)} for r, c in counts.items()]


@router.get("/top-companies")
def get_top_companies(n: int = Query(10)):
    df = load_data()
    top = df.nlargest(n, "Total_ESG_Score")[
        ["Company", "Sector", "Environmental_Score", "Social_Score", "Governance_Score", "Total_ESG_Score", "ESG_Rating"]
    ]
    return top.to_dict(orient="records")


@router.get("/filters")
def get_filter_options():
    df = load_data()
    return {
        "sectors": sorted(df["Sector"].unique().tolist()),
        "countries": sorted(df["Country"].unique().tolist()),
        "ratings": ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"],
    }
