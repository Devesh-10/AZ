export interface FlightSegment {
  departure: string;
  arrival: string;
  departure_time: string;
  arrival_time: string;
  carrier: string;
  flight_number: string;
  duration: string;
}

export interface FlightRisk {
  risk_level: "HIGH" | "MEDIUM" | "LOW";
  reasons: string[];
  recommendation: string;
}

export interface Flight {
  origin: string;
  destination: string;
  price: number;
  currency: string;
  duration: string;
  stops: number;
  segments: FlightSegment[];
  via_middle_east: boolean;
  source: string;
  risk?: FlightRisk;
}

export interface FlightResponse {
  flights: Flight[];
  demo: boolean;
  total: number;
}

export interface DisruptionAlert {
  title: string;
  description: string;
  url: string;
  published: string;
  matched_keywords: string[];
  severity: "HIGH" | "MEDIUM" | "ADVISORY";
}

export interface DisruptionResponse {
  alerts: DisruptionAlert[];
  total: number;
}

export interface Airport {
  code: string;
  city: string;
}
