import { useState, useEffect } from 'react';
import { fetchDocuments, DocSummary } from '../api/chatApi';
import './DocumentSidebar.css';

const TYPE_ICONS: Record<string, string> = {
  SOP: '📋',
  Policy: '📜',
  Training: '🎓',
  'R&D / Clinical': '🔬',
  Compliance: '⚖️',
};

const TYPE_COLORS: Record<string, string> = {
  SOP: '#0ea5e9',
  Policy: '#8b5cf6',
  Training: '#f59e0b',
  'R&D / Clinical': '#10b981',
  Compliance: '#ef4444',
};

export default function DocumentSidebar() {
  const [documents, setDocuments] = useState<DocSummary[]>([]);

  useEffect(() => {
    fetchDocuments().then(setDocuments);
  }, []);

  const grouped = documents.reduce<Record<string, DocSummary[]>>((acc, doc) => {
    (acc[doc.type] ||= []).push(doc);
    return acc;
  }, {});

  return (
    <div className="doc-sidebar">
      <div className="sidebar-header">
        <h3>Document Library</h3>
        <span className="doc-count">{documents.length} docs indexed</span>
      </div>

      <div className="sidebar-body">
        {Object.entries(grouped).map(([type, docs]) => (
          <div key={type} className="doc-group">
            <div className="group-header">
              <span className="group-icon">{TYPE_ICONS[type] || '📄'}</span>
              <span className="group-name">{type}</span>
              <span className="group-badge" style={{ background: TYPE_COLORS[type] || '#6b7280' }}>
                {docs.length}
              </span>
            </div>
            {docs.map((doc) => (
              <div key={doc.id} className="doc-item">
                <span className="doc-id">{doc.id}</span>
                <span className="doc-name">{doc.title}</span>
                <span className="doc-sections">{doc.section_count} sections</span>
              </div>
            ))}
          </div>
        ))}

        {documents.length === 0 && (
          <div className="sidebar-empty">
            <p>Loading documents...</p>
          </div>
        )}
      </div>

      <div className="sidebar-footer">
        <p>Documents are chunked and embedded using sentence-transformers for semantic search.</p>
      </div>
    </div>
  );
}
