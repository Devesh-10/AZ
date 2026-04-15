import type { FlightResponse, DisruptionResponse, Airport } from "./types";

const BASE = "http://localhost:8000";

export async function fetchFlights(params: {
  date?: string;
  origin?: string;
  days?: number;
  adults?: number;
}): Promise<FlightResponse> {
  const sp = new URLSearchParams();
  if (params.date) sp.set("date", params.date);
  if (params.origin) sp.set("origin", params.origin);
  if (params.days) sp.set("days", String(params.days));
  if (params.adults) sp.set("adults", String(params.adults));
  const res = await fetch(`${BASE}/api/flights?${sp}`);
  if (!res.ok) throw new Error("Failed to fetch flights");
  return res.json();
}

export async function fetchDisruptions(): Promise<DisruptionResponse> {
  const res = await fetch(`${BASE}/api/disruptions`);
  if (!res.ok) throw new Error("Failed to fetch disruptions");
  return res.json();
}

export async function fetchAirports(): Promise<Airport[]> {
  const res = await fetch(`${BASE}/api/airports`);
  if (!res.ok) throw new Error("Failed to fetch airports");
  return res.json();
}
