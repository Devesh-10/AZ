import React, { useState } from 'react';
import '../styles/TopHeader.css';

interface TopHeaderProps {
  onFeedbackClick: () => void;
  onReferenceGuideClick: () => void;
}

const TopHeader: React.FC<TopHeaderProps> = ({ onFeedbackClick, onReferenceGuideClick }) => {
  const [mode, setMode] = useState<'Design' | 'Live'>('Design');

  const handleExport = () => {
    alert('Export triggered');
  };

  return (
    <header className="top-header">
      <div className="header-left">
        <div className="logo">AZ</div>
        <h1 className="header-title">Digital Supply Chain Map</h1>
      </div>
      <div className="header-right">
        <div className="toggle-buttons">
          <button
            className={`toggle-btn ${mode === 'Design' ? 'active' : ''}`}
            onClick={() => setMode('Design')}
          >
            Design
          </button>
          <button
            className={`toggle-btn ${mode === 'Live' ? 'active' : ''}`}
            onClick={() => setMode('Live')}
          >
            Live
          </button>
        </div>
        {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
        <a href="#celonis" target="_blank" rel="noopener noreferrer" className="link-btn">
          Celonis
        </a>
        {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
        <a href="#brace" target="_blank" rel="noopener noreferrer" className="link-btn">
          Brace
        </a>
        <button className="header-btn" onClick={handleExport}>
          Export
        </button>
        <button className="header-btn" onClick={onFeedbackClick}>
          Feedback
        </button>
        <button className="header-btn" onClick={onReferenceGuideClick}>
          Reference Guide
        </button>
      </div>
    </header>
  );
};

export default TopHeader;
