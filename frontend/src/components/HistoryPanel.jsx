import { useState, useEffect } from 'react';
import { fetchHistory } from '../lib/api';

export default function HistoryPanel({ projectId, onSelectHistory }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadHistory();
  }, [projectId]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await fetchHistory(projectId);
      setHistory(Array.isArray(data) ? data : (data.history || []));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-error-container text-on-error-container rounded-lg">
        Lỗi tải lịch sử: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <h2 className="text-headline-md font-headline-md text-primary">Lịch sử phân tích Project</h2>
        <button 
          onClick={loadHistory}
          className="flex items-center gap-2 text-primary hover:bg-primary/10 px-4 py-2 rounded-full transition-colors"
        >
          <span className="material-symbols-outlined text-sm">refresh</span>
          Làm mới
        </button>
      </div>

      <div className="space-y-4">
        {history.length === 0 ? (
          <div className="text-center p-12 bg-surface-container-lowest rounded-2xl border border-outline-variant/30 text-on-surface-variant">
            Chưa có lịch sử phân tích nào.
          </div>
        ) : (
          history.map((item, idx) => (
            <div 
              key={item._id || idx} 
              className="bg-surface p-6 rounded-2xl border border-outline-variant shadow-sm hover:shadow-md transition-all group cursor-pointer hover:border-primary/30"
              onClick={() => onSelectHistory && onSelectHistory(item)}
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <span className="inline-block px-2 py-1 bg-primary/10 text-primary rounded text-xs font-bold mb-2">
                    {new Date(item.timestamp).toLocaleString()}
                  </span>
                  <h3 className="text-title-lg font-bold text-on-surface line-clamp-2">
                    {item.requirement}
                  </h3>
                </div>
                <div className="ml-4 flex gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    item.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {item.status}
                  </span>
                </div>
              </div>
              
              <div className="text-body-md text-on-surface-variant line-clamp-3 mb-4">
                {item.story_draft}
              </div>

              <div className="flex flex-wrap gap-2 pt-4 border-t border-outline-variant/30">
                <div className="flex items-center gap-1 text-xs text-outline group-hover:text-primary transition-colors">
                  <span className="material-symbols-outlined text-[14px]">psychology</span>
                  Context: {item.context ? 'Đã phân tích' : 'N/A'}
                </div>
                <div className="flex items-center gap-1 text-xs text-outline group-hover:text-primary transition-colors">
                  <span className="material-symbols-outlined text-[14px]">checklist</span>
                  Evaluation: {item.evaluation ? 'Có' : 'Không'}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
