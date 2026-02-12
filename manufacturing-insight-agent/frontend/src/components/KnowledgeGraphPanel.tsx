import React, { useState, useEffect } from "react";
import { KnowledgeGraph } from "../types";
import { getKnowledgeGraph } from "../api/chatApi";
import "./KnowledgeGraphPanel.css";

const KnowledgeGraphPanel: React.FC = () => {
  const [graph, setGraph] = useState<KnowledgeGraph | null>(null);
  const [activeTab, setActiveTab] = useState<"kpis" | "dimensions" | "relations">(
    "kpis"
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const data = await getKnowledgeGraph();
        setGraph(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setIsLoading(false);
      }
    };

    fetchGraph();
  }, []);

  if (isLoading) {
    return (
      <div className="kg-panel loading">
        <span>Loading knowledge graph...</span>
      </div>
    );
  }

  if (error || !graph) {
    return (
      <div className="kg-panel error">
        <span>⚠️ {error || "Failed to load knowledge graph"}</span>
      </div>
    );
  }

  return (
    <div className="kg-panel">
      <div className="kg-header">
        <h3>🧠 Knowledge Graph</h3>
      </div>

      <div className="kg-tabs">
        <button
          className={`tab ${activeTab === "kpis" ? "active" : ""}`}
          onClick={() => setActiveTab("kpis")}
        >
          KPIs ({graph.kpis.length})
        </button>
        <button
          className={`tab ${activeTab === "dimensions" ? "active" : ""}`}
          onClick={() => setActiveTab("dimensions")}
        >
          Dimensions ({graph.dimensions.length})
        </button>
        <button
          className={`tab ${activeTab === "relations" ? "active" : ""}`}
          onClick={() => setActiveTab("relations")}
        >
          Relations ({graph.relationships.length})
        </button>
      </div>

      <div className="kg-content">
        {activeTab === "kpis" && (
          <div className="kpi-list">
            {graph.kpis.map((kpi) => (
              <div key={kpi.name} className="kpi-card">
                <div className="kpi-header">
                  <span className="kpi-name">{kpi.name}</span>
                  <span className="kpi-unit">{kpi.unit}</span>
                </div>
                <p className="kpi-description">{kpi.description}</p>
                <div className="kpi-meta">
                  <span className="category">{kpi.category}</span>
                  {kpi.relatedKpis.length > 0 && (
                    <span className="related">
                      Related: {kpi.relatedKpis.join(", ")}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === "dimensions" && (
          <div className="dimension-list">
            {graph.dimensions.map((dim) => (
              <div key={dim.name} className="dimension-card">
                <div className="dim-header">
                  <span className="dim-name">{dim.name}</span>
                </div>
                <p className="dim-description">{dim.description}</p>
                <div className="dim-values">
                  {dim.values.slice(0, 5).map((v) => (
                    <span key={v} className="value-chip">
                      {v}
                    </span>
                  ))}
                  {dim.values.length > 5 && (
                    <span className="more-values">
                      +{dim.values.length - 5} more
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === "relations" && (
          <div className="relation-list">
            {graph.relationships.map((rel, i) => (
              <div key={i} className="relation-card">
                <span className="rel-from">{rel.from}</span>
                <span className="rel-arrow">→</span>
                <span className="rel-type">{rel.type}</span>
                <span className="rel-arrow">→</span>
                <span className="rel-to">{rel.to}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeGraphPanel;
