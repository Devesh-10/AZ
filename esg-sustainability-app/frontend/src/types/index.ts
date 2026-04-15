export interface Company {
  Company: string;
  Sector: string;
  Country: string;
  Environmental_Score: number;
  Social_Score: number;
  Governance_Score: number;
  Total_ESG_Score: number;
  ESG_Rating: string;
  Carbon_Emissions_tCO2: number;
  Revenue_Billion_USD: number;
}

export interface Summary {
  total_companies: number;
  avg_environmental: number;
  avg_social: number;
  avg_governance: number;
  avg_total_esg: number;
  top_rated_count: number;
  sectors: number;
  countries: number;
}

export interface SectorData {
  Sector: string;
  Environmental_Score: number;
  Social_Score: number;
  Governance_Score: number;
  Total_ESG_Score: number;
}

export interface RatingData {
  rating: string;
  count: number;
}

export interface FilterOptions {
  sectors: string[];
  countries: string[];
  ratings: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
