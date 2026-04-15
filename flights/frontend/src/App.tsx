import { useState, useEffect } from "react";
import { fetchFlights, fetchDisruptions, fetchAirports } from "./api";
import type { Flight, DisruptionAlert, Airport } from "./types";
import "./App.css";

function formatDuration(d: string): string {
  if (!d) return "—";
  if (d.includes("min")) return d;
  const clean = d.replace("PT", "").replace("P", "");
  let h = 0, m = 0;
  if (clean.includes("H")) {
    const parts = clean.split("H");
    h = parseInt(parts[0]) || 0;
    const rest = parts[1];
    if (rest?.includes("M")) m = parseInt(rest) || 0;
  } else if (clean.includes("M")) {
    m = parseInt(clean) || 0;
  }
  return `${h}h ${m}m`;
}

function formatTime(iso: string): string {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-GB", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch { return iso; }
}

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = { HIGH: "#ef4444", MEDIUM: "#f59e0b", LOW: "#22c55e" };
  return (
    <span className="risk-badge" style={{ background: colors[level] || "#94a3b8" }}>
      {level}
    </span>
  );
}

function DisruptionPanel({ alerts }: { alerts: DisruptionAlert[] }) {
  if (!alerts.length) return null;
  return (
    <div className="disruption-panel">
      <h2>Disruption Alerts</h2>
      {alerts.map((a, i) => (
        <div key={i} className={`alert alert-${a.severity.toLowerCase()}`}>
          <div className="alert-header">
            <RiskBadge level={a.severity} />
            <span className="alert-title">{a.title}</span>
          </div>
          <p>{a.description}</p>
          {a.url && <a href={a.url} target="_blank" rel="noreferrer">Read more</a>}
        </div>
      ))}
    </div>
  );
}

function FlightCard({ flight, rank }: { flight: Flight; rank: number }) {
  const [expanded, setExpanded] = useState(false);
  const risk = flight.risk;

  return (
    <div className={`flight-card ${flight.via_middle_east ? "me-route" : "safe-route"}`}>
      <div className="flight-main" onClick={() => setExpanded(!expanded)}>
        <div className="flight-rank">#{rank}</div>
        <div className="flight-route">
          <span className="airport">{flight.origin}</span>
          <span className="arrow">→</span>
          <span className="airport">{flight.destination}</span>
          {flight.via_middle_east && <span className="me-tag">via Middle East</span>}
        </div>
        <div className="flight-details">
          <span className="stops">{flight.stops === 0 ? "Direct" : `${flight.stops} stop${flight.stops > 1 ? "s" : ""}`}</span>
          <span className="duration">{formatDuration(flight.duration)}</span>
        </div>
        <div className="flight-price">€{flight.price.toFixed(0)}</div>
        {risk && <RiskBadge level={risk.risk_level} />}
        <div className="expand-icon">{expanded ? "▲" : "▼"}</div>
      </div>

      {expanded && (
        <div className="flight-expanded">
          <div className="segments">
            {flight.segments.map((seg, i) => (
              <div key={i} className="segment">
                <div className="seg-flight">{seg.flight_number} ({seg.carrier})</div>
                <div className="seg-route">
                  <span>{seg.departure} {formatTime(seg.departure_time)}</span>
                  <span className="seg-arrow">→</span>
                  <span>{seg.arrival} {formatTime(seg.arrival_time)}</span>
                </div>
                <div className="seg-dur">{formatDuration(seg.duration)}</div>
              </div>
            ))}
          </div>
          {risk && (
            <div className={`risk-detail risk-${risk.risk_level.toLowerCase()}`}>
              {risk.reasons.map((r, i) => <p key={i}>• {r}</p>)}
              <p className="recommendation">{risk.recommendation}</p>
            </div>
          )}
          <div className="flight-source">Source: {flight.source}</div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [flights, setFlights] = useState<Flight[]>([]);
  const [alerts, setAlerts] = useState<DisruptionAlert[]>([]);
  const [airports, setAirports] = useState<Airport[]>([]);
  const [loading, setLoading] = useState(false);
  const [isDemo, setIsDemo] = useState(false);
  const [origin, setOrigin] = useState("");
  const [date, setDate] = useState("");
  const [days, setDays] = useState(3);
  const [filterSafe, setFilterSafe] = useState(false);

  useEffect(() => {
    fetchAirports().then(setAirports).catch(() => {});
    fetchDisruptions().then((d) => setAlerts(d.alerts)).catch(() => {});
  }, []);

  async function search() {
    setLoading(true);
    try {
      const res = await fetchFlights({ date: date || undefined, origin: origin || undefined, days });
      setFlights(res.flights);
      setIsDemo(res.demo);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { search(); }, []);

  const displayed = filterSafe ? flights.filter((f) => !f.via_middle_east) : flights;
  const safeCount = flights.filter((f) => !f.via_middle_east).length;
  const meCount = flights.filter((f) => f.via_middle_east).length;
  const cheapest = flights[0];
  const cheapestSafe = flights.find((f) => !f.via_middle_east);

  return (
    <div className="app">
      <header>
        <div className="logo">Flight Agent</div>
        <div className="subtitle">Cheapest India → Dublin · Disruption Monitor</div>
      </header>

      {isDemo && (
        <div className="demo-banner">
          Demo Mode — Configure Amadeus API keys in .env for live flight data
        </div>
      )}

      <DisruptionPanel alerts={alerts} />

      <div className="search-bar">
        <select value={origin} onChange={(e) => setOrigin(e.target.value)}>
          <option value="">All Airports</option>
          {airports.map((a) => (
            <option key={a.code} value={a.code}>{a.city} ({a.code})</option>
          ))}
        </select>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} placeholder="Date" />
        <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
          {[1, 3, 5, 7, 14].map((d) => (
            <option key={d} value={d}>{d} day{d > 1 ? "s" : ""}</option>
          ))}
        </select>
        <button className="search-btn" onClick={search} disabled={loading}>
          {loading ? "Searching..." : "Search Flights"}
        </button>
      </div>

      {flights.length > 0 && (
        <div className="summary-cards">
          <div className="summary-card best">
            <div className="summary-label">Cheapest Overall</div>
            <div className="summary-price">€{cheapest?.price.toFixed(0)}</div>
            <div className="summary-route">{cheapest?.origin} → DUB</div>
            {cheapest?.via_middle_east && <span className="me-tag small">via ME</span>}
          </div>
          {cheapestSafe && (
            <div className="summary-card safe">
              <div className="summary-label">Cheapest Safe Route</div>
              <div className="summary-price">€{cheapestSafe.price.toFixed(0)}</div>
              <div className="summary-route">{cheapestSafe.origin} → DUB</div>
            </div>
          )}
          <div className="summary-card stat">
            <div className="summary-label">Routes Found</div>
            <div className="summary-price">{flights.length}</div>
            <div className="summary-route">{safeCount} safe · {meCount} via ME</div>
          </div>
        </div>
      )}

      <div className="filter-bar">
        <label>
          <input type="checkbox" checked={filterSafe} onChange={(e) => setFilterSafe(e.target.checked)} />
          Show only safe routes (avoid Middle East)
        </label>
        <span className="result-count">{displayed.length} flights</span>
      </div>

      <div className="flights-list">
        {loading && <div className="loading">Searching flights across Indian airports...</div>}
        {!loading && displayed.length === 0 && <div className="empty">No flights found. Try adjusting your search.</div>}
        {displayed.map((f, i) => (
          <FlightCard key={`${f.origin}-${f.price}-${i}`} flight={f} rank={i + 1} />
        ))}
      </div>

      <footer>
        <p>Prices are indicative. Book directly on airline websites for best fares.</p>
        <p>Disruption data based on news monitoring — always check airline status before travel.</p>
      </footer>
    </div>
  );
}
