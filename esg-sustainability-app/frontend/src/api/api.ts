import axios from "axios";
import type { Company, Summary, SectorData, RatingData, FilterOptions } from "../types";

const api = axios.create({ baseURL: "/api" });

export async function fetchSummary(): Promise<Summary> {
  const { data } = await api.get("/dashboard/summary");
  return data;
}

export async function fetchCompanies(params?: {
  sector?: string;
  country?: string;
  rating?: string;
  search?: string;
  sort_by?: string;
  order?: string;
}): Promise<Company[]> {
  const { data } = await api.get("/dashboard/companies", { params });
  return data;
}

export async function fetchSectors(): Promise<SectorData[]> {
  const { data } = await api.get("/dashboard/sectors");
  return data;
}

export async function fetchRatings(): Promise<RatingData[]> {
  const { data } = await api.get("/dashboard/ratings");
  return data;
}

export async function fetchTopCompanies(n = 10): Promise<Company[]> {
  const { data } = await api.get("/dashboard/top-companies", { params: { n } });
  return data;
}

export async function fetchFilters(): Promise<FilterOptions> {
  const { data } = await api.get("/dashboard/filters");
  return data;
}

export async function sendChatMessage(message: string): Promise<string> {
  const { data } = await api.post("/chat/", { message });
  return data.response;
}
