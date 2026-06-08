import { useState, useEffect } from 'react';
import { fetchSprintBoard } from '../lib/api';

export default function SprintBoardPanel({ isActive, projectId }) {
  const [boardData, setBoardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isActive) {
      loadBoard();
    }
  }, [isActive, projectId]);

  const loadBoard = async () => {
    try {
      setLoading(true);
      const data = await fetchSprintBoard(projectId);
      setBoardData(data);
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
        Lỗi tải Sprint Board: {error}
      </div>
    );
  }

  if (!boardData?.sprint) {
    return (
      <div className="text-center p-12 bg-surface-container-lowest rounded-2xl border border-outline-variant/30 text-on-surface-variant">
        Chưa có Sprint nào đang Active trên Jira. Vui lòng Start một Sprint trên Jira Board của bạn.
      </div>
    );
  }

  const { sprint, issues } = boardData;

  // Group issues by status
  const columns = {
    'To Do': issues.filter(i => i.status.toLowerCase().includes('to do') || i.status.toLowerCase().includes('open')),
    'In Progress': issues.filter(i => i.status.toLowerCase().includes('in progress')),
    'Done': issues.filter(i => i.status.toLowerCase().includes('done') || i.status.toLowerCase().includes('closed'))
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 h-full flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-headline-md font-headline-md text-primary flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">skateboarding</span>
            {sprint.name}
          </h2>
          <p className="text-on-surface-variant text-label-md mt-1">
            Mục tiêu: {sprint.goal || 'Không có'} | Bắt đầu: {sprint.start_date ? new Date(sprint.start_date).toLocaleDateString() : 'N/A'}
          </p>
        </div>
        <button 
          onClick={loadBoard}
          className="flex items-center gap-2 bg-primary/10 text-primary hover:bg-primary/20 px-4 py-2 rounded-full transition-colors"
        >
          <span className="material-symbols-outlined text-sm">sync</span>
          Đồng bộ Jira
        </button>
      </div>

      <div className="flex-1 overflow-x-auto">
        <div className="flex gap-6 h-full min-w-max pb-4">
          {Object.entries(columns).map(([colName, colIssues]) => (
            <div key={colName} className="w-[350px] flex flex-col bg-surface-container-low rounded-2xl p-4 border border-outline-variant">
              <div className="flex justify-between items-center mb-4 px-2">
                <h3 className="font-bold text-title-md text-on-surface uppercase tracking-wider text-sm">{colName}</h3>
                <span className="bg-surface-container-high px-2 py-1 rounded-full text-xs font-bold text-on-surface-variant">
                  {colIssues.length}
                </span>
              </div>
              
              <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar px-2 pb-2">
                {colIssues.map(issue => (
                  <div key={issue.key} className="bg-surface p-4 rounded-xl shadow-sm border border-outline-variant hover:border-primary/50 transition-colors cursor-default">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">
                        {issue.key}
                      </span>
                      <span className="material-symbols-outlined text-outline text-[16px]">
                        {issue.type === 'Story' ? 'bookmark' : 'task'}
                      </span>
                    </div>
                    <p className="text-body-md text-on-surface font-medium line-clamp-3 mb-3">
                      {issue.summary}
                    </p>
                    <div className="flex justify-between items-center">
                      <div className="w-6 h-6 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container text-[10px] font-bold" title={issue.assignee || 'Unassigned'}>
                        {issue.assignee ? issue.assignee.substring(0, 2).toUpperCase() : '??'}
                      </div>
                      {issue.priority && (
                        <span className="text-[10px] uppercase font-bold text-outline border border-outline-variant px-1 rounded">
                          {issue.priority}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                
                {colIssues.length === 0 && (
                  <div className="h-24 border-2 border-dashed border-outline-variant/50 rounded-xl flex items-center justify-center text-outline text-sm">
                    Kéo thả trên Jira
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
