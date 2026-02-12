import React from 'react';
import { stages } from '../data/mapData';
import StageColumn from './StageColumn';
import FlowConnections from './FlowConnections';
import '../styles/MapCanvas.css';

interface MapCanvasProps {
  showControls: boolean;
}

const MapCanvas: React.FC<MapCanvasProps> = ({ showControls }) => {
  return (
    <div className={`map-canvas ${showControls ? 'with-controls' : ''}`}>
      <FlowConnections />
      <div className="stages-container">
        {stages.map((stage) => (
          <StageColumn key={stage.id} stage={stage} />
        ))}
      </div>
    </div>
  );
};

export default MapCanvas;
