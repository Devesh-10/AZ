import React from 'react';
import { brands } from '../data/mapData';
import '../styles/BrandHeader.css';

interface BrandHeaderProps {
  selectedBrand: string;
  onBrandChange: (brand: string) => void;
  showControls: boolean;
  onToggleControls: () => void;
  onShowNotes: () => void;
}

const BrandHeader: React.FC<BrandHeaderProps> = ({
  selectedBrand,
  onBrandChange,
  showControls,
  onToggleControls,
  onShowNotes,
}) => {
  const handleMaterialFlow = () => {
    console.log('Go to Material Flow clicked');
  };

  return (
    <div className="brand-header">
      <div className="brand-header-left">
        <label className="brand-label">Brand</label>
        <select
          className="brand-dropdown"
          value={selectedBrand}
          onChange={(e) => onBrandChange(e.target.value)}
        >
          {brands.map((brand) => (
            <option key={brand} value={brand}>
              {brand}
            </option>
          ))}
        </select>
        <h2 className="flow-heading">{selectedBrand} Manufacturing Flow</h2>
      </div>
      <div className="brand-header-right">
        <button className="brand-btn" onClick={handleMaterialFlow}>
          Go to Material Flow
        </button>
        <button className="brand-btn" onClick={onShowNotes}>
          Show Notes
        </button>
        <button className="brand-btn control-toggle" onClick={onToggleControls}>
          {showControls ? 'Hide Control' : 'Show Control'}
        </button>
      </div>
    </div>
  );
};

export default BrandHeader;
