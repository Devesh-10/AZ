import React, { useState } from 'react';
import { Box } from '../data/mapData';
import '../styles/StageBox.css';

interface StageBoxProps {
  box: Box;
  stageId: string;
}

const StageBox: React.FC<StageBoxProps> = ({ box, stageId }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const getStatusIcon = () => {
    switch (box.statusType) {
      case 'success':
        return (
          <div className="status-icon success">
            <span>✓</span>
          </div>
        );
      case 'warning':
        return (
          <div
            className="status-icon warning"
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
          >
            <span>i</span>
          </div>
        );
      case 'danger':
        return (
          <div
            className="status-icon danger"
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
          >
            <span>i</span>
          </div>
        );
      default:
        return null;
    }
  };

  const isCustomerMarket = stageId === 'customer-market';

  return (
    <div
      className="stage-box"
      id={box.id}
      style={{ borderLeftColor: box.borderColor }}
    >
      <div className="box-header">
        <span className="box-title">{box.title}</span>
        {getStatusIcon()}
        {showTooltip && box.tooltipText && (
          <div className="tooltip">
            <p>{box.tooltipText}</p>
            <div className="tooltip-buttons">
              <button className="tooltip-btn" onClick={() => console.log('Generate Simulation')}>
                Generate Simulation
              </button>
              <button className="tooltip-btn" onClick={() => console.log('Generate Recommendation')}>
                Generate Recommendation
              </button>
            </div>
          </div>
        )}
      </div>
      <div className="box-materials">
        {box.materials.map((material, idx) => (
          <div key={idx} className="material-item">
            <div className="material-name">{material.name}</div>
            <div className="material-placeholder">{material.placeholder}</div>
          </div>
        ))}
      </div>
      {box.hasKpi && (
        <div className="kpi-section">
          <div className="kpi-row">
            <span className={`kpi-chip ${isCustomerMarket ? 'dark-blue' : 'peach'}`}>12</span>
            <span className={`kpi-chip ${isCustomerMarket ? 'dark-blue' : 'peach'}`}>7</span>
            <span className={`kpi-chip ${isCustomerMarket ? 'dark-blue' : 'peach'}`}>98%</span>
          </div>
          <div className="kpi-row">
            <span className={`kpi-chip ${isCustomerMarket ? 'dark-blue' : 'pink'}`}>3d</span>
            <span className={`kpi-chip ${isCustomerMarket ? 'dark-blue' : 'pink'}`}>5</span>
            <span className={`kpi-chip ${isCustomerMarket ? 'dark-blue' : 'pink'}`}>1.2</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default StageBox;
