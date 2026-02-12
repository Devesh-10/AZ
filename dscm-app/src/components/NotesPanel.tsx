import React from 'react';
import '../styles/NotesPanel.css';

interface NotesPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const NotesPanel: React.FC<NotesPanelProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="notes-panel">
      <div className="notes-header">
        <h3>Notes</h3>
        <button className="close-btn" onClick={onClose}>
          ✕
        </button>
      </div>
      <div className="notes-content">
        <p className="placeholder-text">
          Notes panel placeholder. This area would contain important notes and
          annotations related to the supply chain map.
        </p>
        <div className="note-item">
          <strong>Note 1:</strong> Review API component delays
        </div>
        <div className="note-item">
          <strong>Note 2:</strong> Formulation Plant B requires attention
        </div>
        <div className="note-item">
          <strong>Note 3:</strong> Customer market Box2 risk assessment pending
        </div>
      </div>
    </div>
  );
};

export default NotesPanel;
