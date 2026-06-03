import { useState } from 'react';

export default function DebugJsonPanel({ data }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!data) return null;

  return (
    <div className="panel debug-panel">
      <div className="debug-header" onClick={() => setIsOpen(!isOpen)}>
        <h2>Debug: Raw JSON Response</h2>
        <span className="toggle-icon">{isOpen ? '▼' : '▶'}</span>
      </div>
      
      {isOpen && (
        <div className="debug-content">
          <pre>
            <code>{JSON.stringify(data, null, 2)}</code>
          </pre>
        </div>
      )}
    </div>
  );
}
