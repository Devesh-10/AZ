import React, { useState } from 'react';
import { organizationLegend, teamLegend } from '../data/mapData';
import '../styles/ControlsBar.css';

const ControlsBar: React.FC = () => {
  const [filters, setFilters] = useState({
    inventory: false,
    production: false,
    customer: false,
  });

  const handleFilterChange = (filter: keyof typeof filters) => {
    setFilters((prev) => ({
      ...prev,
      [filter]: !prev[filter],
    }));
  };

  return (
    <div className="controls-bar">
      <div className="controls-section">
        <h3 className="section-label">Data Filters</h3>
        <div className="filter-checkboxes">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.inventory}
              onChange={() => handleFilterChange('inventory')}
            />
            <span>Inventory</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.production}
              onChange={() => handleFilterChange('production')}
            />
            <span>Production</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.customer}
              onChange={() => handleFilterChange('customer')}
            />
            <span>Customer</span>
          </label>
        </div>
      </div>

      <div className="controls-divider" />

      <div className="controls-section">
        <h3 className="section-label">Organization Key</h3>
        <div className="legend-chips">
          {organizationLegend.map((item) => (
            <div
              key={item.label}
              className="legend-chip"
              style={{ borderColor: item.color }}
            >
              {item.label}
            </div>
          ))}
        </div>
      </div>

      <div className="controls-divider" />

      <div className="controls-section">
        <h3 className="section-label">Team Legend</h3>
        <div className="team-chips">
          {teamLegend.map((team) => (
            <div key={team} className="team-chip">
              {team}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ControlsBar;
