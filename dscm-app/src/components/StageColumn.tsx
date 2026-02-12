import React from 'react';
import { Stage } from '../data/mapData';
import StageBox from './StageBox';
import '../styles/StageColumn.css';

interface StageColumnProps {
  stage: Stage;
}

const StageColumn: React.FC<StageColumnProps> = ({ stage }) => {
  return (
    <div className="stage-column">
      <div className="stage-label" style={{ backgroundColor: stage.labelColor }}>
        {stage.name}
      </div>
      <div className="stage-container">
        {stage.boxes.map((box) => (
          <StageBox key={box.id} box={box} stageId={stage.id} />
        ))}
      </div>
    </div>
  );
};

export default StageColumn;
