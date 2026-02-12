import React, { useState } from 'react';
import TopHeader from './components/TopHeader';
import BrandHeader from './components/BrandHeader';
import ControlsBar from './components/ControlsBar';
import MapCanvas from './components/MapCanvas';
import ChatAssist from './components/ChatAssist';
import Modal from './components/Modal';
import NotesPanel from './components/NotesPanel';
import './App.css';

function App() {
  const [selectedBrand, setSelectedBrand] = useState('Brand A');
  const [showControls, setShowControls] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [showReferenceModal, setShowReferenceModal] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');

  const handleFeedbackSubmit = () => {
    alert('Feedback submitted: ' + feedbackText);
    setFeedbackText('');
    setShowFeedbackModal(false);
  };

  return (
    <div className="app">
      <TopHeader
        onFeedbackClick={() => setShowFeedbackModal(true)}
        onReferenceGuideClick={() => setShowReferenceModal(true)}
      />

      <BrandHeader
        selectedBrand={selectedBrand}
        onBrandChange={setSelectedBrand}
        showControls={showControls}
        onToggleControls={() => setShowControls(!showControls)}
        onShowNotes={() => setShowNotes(!showNotes)}
      />

      {showControls && <ControlsBar />}

      <MapCanvas showControls={showControls} />

      <ChatAssist />

      <NotesPanel isOpen={showNotes} onClose={() => setShowNotes(false)} />

      <Modal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        title="Feedback"
      >
        <p>We value your feedback! Please share your thoughts about the Digital Supply Chain Map.</p>
        <textarea
          placeholder="Enter your feedback here..."
          value={feedbackText}
          onChange={(e) => setFeedbackText(e.target.value)}
        />
        <button onClick={handleFeedbackSubmit}>Submit Feedback</button>
      </Modal>

      <Modal
        isOpen={showReferenceModal}
        onClose={() => setShowReferenceModal(false)}
        title="Reference Guide"
      >
        <p><strong>Digital Supply Chain Map - Reference Guide</strong></p>
        <p>
          The Digital Supply Chain Map (DSCM) provides a visual representation of your
          manufacturing flow from raw materials to customer markets.
        </p>
        <p><strong>Stages:</strong></p>
        <ul>
          <li><strong>RSM</strong> - Raw/Starting Materials</li>
          <li><strong>Intermediate</strong> - Intermediate processing</li>
          <li><strong>API</strong> - Active Pharmaceutical Ingredient</li>
          <li><strong>Formulation</strong> - Drug formulation</li>
          <li><strong>Packaging</strong> - Final packaging</li>
          <li><strong>Customer Market</strong> - Distribution to markets</li>
        </ul>
        <p><strong>Status Icons:</strong></p>
        <ul>
          <li>Green checkmark - Normal operation</li>
          <li>Amber info icon - Potential risk</li>
          <li>Red info icon - High risk</li>
        </ul>
        <p><strong>Arrow Colors:</strong></p>
        <ul>
          <li>Black - Normal flow</li>
          <li>Amber - Potential risk path</li>
          <li>Red - High risk path</li>
        </ul>
      </Modal>
    </div>
  );
}

export default App;
